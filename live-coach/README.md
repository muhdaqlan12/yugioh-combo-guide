# Blue-Eyes Live Coach V1 (Windows, offline)

A free personal **manual-state** companion to Yu-Gi-Oh! Master Duel, built with Python and PySide6. Uses the existing Blue-Eyes Primite deck JSON from this repository.

## What V1 does

- Compact always-on-top window, movable and minimizable.
- Opening-hand selector: exactly five cards; validates deck copy counts.
- Starter checklists selected from the opening hand (Ether Beryl, Sage, Wishes, Lordly Lode).
- Interactive scrollable combo decision map: opening hand → available starter branches → resolved / negated handling. Click any starter to load its checklist.
- Resolved advances the checklist; Negated **pauses** the checklist; Replan clears the route rather than pretending a negated effect resolved.
- Extra Deck counter per card, with + / −, enforcing the recorded deck copy limits.
- Automatic local save in `%USERPROFILE%\.blue_eyes_live_coach\state.json` (no account or cloud).
- The original 18-step and 13-step expert combos are accessible as **UNVERIFIED REFERENCE** routes with explicit warnings.

## What V1 does NOT do

- **No automatic or continuous screenshot recognition**; no vision model included.
- No direct connection to Master Duel, no memory access, no gameplay automation.
- No complete rules simulation or guaranteed legal combo recommendation.
- No guarantee the original reference combos work from the supplied opening hand.
- A Resolved click records your manual confirmation; it does not inspect the in-game state.

Use this tool as a learning checklist and verify every activation, summon and material in the game. Third-party assistance and overlay usage should be checked against applicable Konami game terms, especially in online play.

## Run on Windows

1. Install Python 3.11 or 3.12 from python.org, ensuring Python is added to PATH.
2. Download this branch as ZIP from GitHub, extract, and open a terminal in `live-coach`.
3. Run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, use `.venv\Scripts\python.exe app.py` instead, and `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

Run Master Duel in Borderless Windowed mode for a more predictable always-on-top overlay. Drag the overlay by its Windows title bar. Click **Combo map** for the larger visual tree.

## Build Windows EXE

In the same virtual environment, run:

```powershell
python -m PyInstaller --clean --noconfirm packaging/blue_eyes_live_coach.spec
```

The one-file executable is produced at `dist\BlueEyesLiveCoach.exe`. The JSON deck is bundled; no internet needed at runtime. Build on Windows to produce a Windows executable. This repo contains **source + build configuration**, not a precompiled Windows EXE.

## Tests

From `live-coach`:

```powershell
python -m unittest discover -s tests -v
```

## Source layout

- `app.py` — PySide6 overlay, selectors, graph, persistence UI.
- `core/engine.py` — deck loading, starter checklists, state machine.
- `data/blue-eyes-primite.json` — copy of the original repository deck data.
- `tests/test_engine.py` — offline engine tests.
- `packaging/blue_eyes_live_coach.spec` — PyInstaller configuration.

## Next iteration (not implemented)

A continuous screen-capture pipeline (Windows Graphics Capture or mss), recognition confidence checking, manual correction, duel event reconciliation, and legal state-aware combo generation. The vision system should operate only on pixels, never inject inputs or inspect the game process.
