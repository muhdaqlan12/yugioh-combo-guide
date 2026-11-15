import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.engine import CoachEngine, load_deck, DuelState

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.deck=load_deck()
        self.engine=CoachEngine(self.deck)

    def test_deck_totals(self):
        self.assertEqual(sum(c for _,c in self.deck["mainDeck"]),40)
        self.assertEqual(sum(c for _,c in self.deck["extraDeck"]),15)

    def test_hand_quantity_limit(self):
        with self.assertRaises(ValueError):
            self.engine.select_hand(["Blue-Eyes White Dragon"]*5)

    def test_starters_from_hand(self):
        self.engine.select_hand([
            "Primite Dragon Ether Beryl","Sage with Eyes of Blue",
            "Maiden of White","Wishes for Eyes of Blue","Ash Blossom & Joyous Spring"])
        ids={r.id for r in self.engine.available_routes()}
        self.assertEqual(ids,{"ether","sage","wishes"})

    def test_negate_pauses(self):
        self.engine.select_hand([
            "Primite Dragon Ether Beryl","Sage with Eyes of Blue",
            "Maiden of White","Wishes for Eyes of Blue","Ash Blossom & Joyous Spring"])
        self.engine.select_route("ether")
        self.engine.negate()
        self.assertTrue(self.engine.state.paused)
        self.assertEqual(self.engine.state.index,0)
        self.engine.resolve()
        self.assertEqual(self.engine.state.index,1 if False else 0)

    def test_resolve_and_replan(self):
        self.engine.select_hand([
            "Primite Dragon Ether Beryl","Sage with Eyes of Blue",
            "Maiden of White","Wishes for Eyes of Blue","Ash Blossom & Joyous Spring"])
        self.engine.select_route("ether")
        self.engine.resolve()
        self.assertEqual(self.engine.state.index,1)
        self.engine.retry_or_replan()
        self.assertEqual(self.engine.state.route_id,"")

    def test_extra_copy_limit(self):
        self.engine.mark_extra("Linkuriboh")
        with self.assertRaises(ValueError):
            self.engine.mark_extra("Linkuriboh")
        self.engine.undo_extra("Linkuriboh")
        self.assertEqual(self.engine.state.extra_used["Linkuriboh"],0)

    def test_state_json_round_trip(self):
        self.engine.state.hand=["Sage with Eyes of Blue"]
        state=DuelState.from_json(self.engine.state.to_json())
        self.assertEqual(state.hand,["Sage with Eyes of Blue"])

if __name__=="__main__":
    unittest.main()
