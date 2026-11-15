"""Offline deck, route and duel-state logic. No automated Master Duel interaction."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "data" / "blue-eyes-primite.json"

def load_deck(path: Path = DECK_PATH) -> dict:
    with path.open(encoding="utf-8") as stream:
        deck = json.load(stream)
    assert sum(n for _, n in deck["mainDeck"]) == 40, "Main Deck must have 40 cards"
    assert sum(n for _, n in deck["extraDeck"]) == 15, "Extra Deck must have 15 cards"
    return deck

@dataclass
class Step:
    title: str
    instruction: str
    note: str = ""
    tag: str = "CHECK"
    extra_used: str = ""

@dataclass
class Route:
    id: str
    title: str
    starter: str
    steps: list[Step]
    status: str = "Guided checklist — verify against game state"
    requires: list[str] = field(default_factory=list)

@dataclass
class DuelState:
    hand: list[str] = field(default_factory=list)
    route_id: str = ""
    index: int = 0
    history: list[dict] = field(default_factory=list)
    extra_used: dict[str, int] = field(default_factory=dict)
    paused: bool = False

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, value: dict) -> DuelState:
        return cls(**{k: value[k] for k in cls.__dataclass_fields__ if k in value})

def guided_routes(deck: dict) -> list[Route]:
    """These are prompts, not a card-rule simulator. They do not auto-spend resources."""
    routes = [
        Route("ether", "Primite Ether Beryl — starter checks", "Primite Dragon Ether Beryl", [
            Step("Review Normal Summon", "Check whether Primite Dragon Ether Beryl can be Normal Summoned and whether you have already used your Normal Summon.", "Only proceed when the game actually permits the summon.", "SUMMON"),
            Step("Resolve Ether Beryl", "Activate Ether Beryl's relevant effect if available; confirm its exact result in Master Duel.", "Do not assume a Set/search succeeded if negated.", "EFFECT"),
            Step("Inspect Primite options", "Check which Primite Spells/Traps are now accessible, and whether their activation conditions are met.", "Use the actual available effect text and game prompts.", "OPTIONS"),
            Step("Check Link conversion", "If you control the required Link material and Spirit with Eyes of Blue is legal, you may choose that line.", "Verify materials and Extra Monster Zone placement.", "LINK"),
            Step("Choose next line", "Review the currently available cards, Extra Deck and summon restrictions; choose a verified follow-up or stop.", "Do not infer missing Blue-Eyes bodies or extra Normal Summons.", "DECISION")
        ]),
        Route("sage", "Sage — Blue-Eyes access checks", "Sage with Eyes of Blue", [
            Step("Check Sage Normal Summon", "If you can Normal Summon Sage with Eyes of Blue, do so only after deciding whether you need that Normal Summon for another starter.", "The coach cannot see your actual field.", "SUMMON"),
            Step("Confirm Sage search", "If Sage's search effect resolves, confirm which Level 1 LIGHT Tuner was added to hand.", "Do not assume Maiden is available unless you selected it.", "SEARCH"),
            Step("Plan extension", "Inspect Maiden of White, Wishes for Eyes of Blue, Mausoleum of White and any other cards actually available.", "Some effects require an existing field or Graveyard setup.", "OPTIONS"),
            Step("Validate Synchro", "Before a Blue-Eyes Spirit Dragon Synchro Summon, confirm the correct Tuner, non-Tuner, Levels and summon restrictions.", "A target Extra Deck card is not proof its materials exist.", "SYNCHRO")
        ]),
        Route("wishes", "Wishes — Blue-Eyes setup checks", "Wishes for Eyes of Blue", [
            Step("Review Wishes activation", "Check the current legal activation conditions and decide whether to activate Wishes for Eyes of Blue.", "Read the card text in the game.", "SPELL"),
            Step("Confirm resolution", "Record which card or cards were actually moved to hand, Graveyard or field after the effect resolves.", "Avoid treating a negated effect as successful.", "CHECK"),
            Step("Choose follow-up", "Identify a summon or extension that is legal using only your confirmed resources.", "Any extra-deck summon must satisfy its materials.", "OPTIONS")
        ]),
        Route("lode", "Lordly Lode — Primite setup checks", "Primite Lordly Lode", [
            Step("Activate Lordly Lode", "Check whether Primite Lordly Lode is playable now, then activate it if your chosen line requires it.", "Resolve any game prompts first.", "SPELL"),
            Step("Confirm card access", "If the effect resolves, confirm the specific Primite card obtained or accessed.", "The coach does not assume Drillbeam was added.", "CHECK"),
            Step("Check Normal Monster", "If you intend to use a Primite summon effect, confirm a valid Normal Monster and every activation restriction.", "Do not assume Blue-Eyes is in GY or available in Deck.", "SUMMON")
        ])
    ]
    for combo in deck.get("combos", []):
        raw = combo.get("steps", [])
        steps = [Step(
            s.get("title", "Reference step"),
            s.get("action", ""),
            s.get("why", ""),
            s.get("tag", "REFERENCE")
        ) for s in raw]
        routes.append(Route("ref:" + combo["id"], combo.get("name", "Reference"), "Reference only",
            steps, status="UNVERIFIED REFERENCE — individual steps may be illegal or require extra setup",
            requires=combo.get("requires", [])))
    return routes

class CoachEngine:
    def __init__(self, deck: dict, state: DuelState | None = None):
        self.deck = deck
        self.routes = guided_routes(deck)
        self.state = state or DuelState()

    def available_routes(self) -> list[Route]:
        hand = self.state.hand
        result = [r for r in self.routes if r.starter in hand and not r.id.startswith("ref:")]
        # Reference lines never auto-start from loose hand requirements.
        return result

    def route(self) -> Route | None:
        return next((r for r in self.routes if r.id == self.state.route_id), None)

    def select_hand(self, cards: list[str]) -> None:
        counts = dict(self.deck["mainDeck"])
        if len(cards) != 5:
            raise ValueError("Exactly five opening-hand cards are required.")
        for name in set(cards):
            if cards.count(name) > counts.get(name, 0):
                raise ValueError(f"Too many copies of {name} in hand.")
        self.state = DuelState(hand=list(cards))

    def select_route(self, route_id: str) -> None:
        route = next((r for r in self.routes if r.id == route_id), None)
        if not route:
            raise ValueError("Unknown route.")
        if not route_id.startswith("ref:") and route.starter not in self.state.hand:
            raise ValueError("Starter is not in opening hand.")
        self.state.route_id = route_id
        self.state.index = 0
        self.state.paused = False
        self.state.history = []

    def current_step(self) -> Step | None:
        route = self.route()
        if not route or self.state.index >= len(route.steps):
            return None
        return route.steps[self.state.index]

    def resolve(self) -> None:
        step = self.current_step()
        if step is None or self.state.paused:
            return
        self.state.history.append({"step": self.state.index, "outcome": "resolved", "title": step.title})
        self.state.index += 1
        self.state.paused = False

    def negate(self) -> None:
        step = self.current_step()
        if step is None:
            return
        self.state.history.append({"step": self.state.index, "outcome": "negated", "title": step.title})
        self.state.paused = True
        # Intentionally DON'T continue a line after a failed prerequisite.

    def retry_or_replan(self) -> None:
        self.state.paused = False
        self.state.route_id = ""
        self.state.index = 0

    def mark_extra(self, name: str) -> None:
        quantities = dict(self.deck["extraDeck"])
        used = self.state.extra_used.get(name, 0)
        if name not in quantities or used >= quantities[name]:
            raise ValueError("No unused copies left in the Extra Deck tracker.")
        self.state.extra_used[name] = used + 1

    def undo_extra(self, name: str) -> None:
        used = self.state.extra_used.get(name, 0)
        if used > 0:
            self.state.extra_used[name] = used - 1
