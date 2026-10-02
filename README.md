# Yu-Gi-Oh! Combo Guide — Blue-Eyes Primite

A lightweight browser-based combo trainer for the Blue-Eyes Primite deck from Master Duel.

## Current version

The app is a static prototype, so **no npm/node installation is required**.

### Easiest way to use it

1. Open the repository on GitHub.
2. Open `index.html`.
3. Download the file if you want to run it locally.
4. Double-click `index.html` and open it in Chrome/Edge.

You can also clone the repository:

```bash
git clone https://github.com/muhdaqlan12/yugioh-combo-guide.git
cd yugioh-combo-guide
```

Then open `index.html` in your browser.

## Using it while playing Master Duel

Put Master Duel on one monitor and the Combo Guide on the other.

1. Open **Combos**.
2. Select a combo line.
3. Start the combo in Master Duel.
4. Click **Next** after performing each action.
5. Use **Why?** when you want the reason for the current action.
6. If you make it to the end, the app shows `Combo complete`.

Keyboard shortcuts:

- `Space` — next step
- `R` — restart
- `P` — practice mode

## Included deck

The current deck is the supplied **Blue Eyes, primite** list:

- Main Deck: 40
- Extra Deck: 15
- 3 Sage with Eyes of Blue
- 3 Maiden of White
- 3 Primite Dragon Ether Beryl
- 2 Blue-Eyes White Dragon
- 3 Ash Blossom & Joyous Spring
- 3 Effect Veiler
- 2 Maxx "C"
- 3 Wishes for Eyes of Blue
- 3 Primite Lordly Lode
- 1 Primite Drillbeam
- 1 Roar of the Blue-Eyed Dragons
- 1 Mausoleum of White
- 1 Crossout Designator
- 2 Called by the Grave
- 1 Synchro Rumble
- 1 Ultimate Fusion
- 1 True Light
- 3 Infinite Impermanence
- 3 Dominus Purge

The Extra Deck data is also included in `data/blue-eyes-primite.json`.

## Combo data

`data/blue-eyes-primite.json` contains the deck and the initial combo library.

The first combo is the Ether Beryl + Sage core line. The app intentionally marks some later continuation/interrupt branches as work in progress rather than inventing a line. These will be expanded and tested as the deck is developed.

## Roadmap

- Exact card images
- Exact Master Duel opening-hand simulator
- Branches for Ash Blossom / Effect Veiler / Infinite Impermanence / Maxx "C"
- More one-card and two-card lines
- Going-second lines
- Alternative endboards
- Interactive decision checking for every combo step
- Combo editor so custom lines can be added without editing code
