# Chaos League — Running & Usage Guide

This document explains how to run Chaos League tournaments, how determinism and randomness work, how results are generated, and what a bot **must** implement to participate correctly.

Run everything from the project root.

---

## 1. Running a Tournament

To run a full tournament:

```bash
python tournament.py
```

This will:
- Load all bots from `bots/`
- Run a round-robin tournament
- Print a leaderboard
- Optionally write results to disk (see COMPETITION mode)

---

## 2. Bot Requirements (Critical)

Every bot **must** follow this structure to work correctly.

### File Location
- Place the bot in the `bots/` directory
- File name becomes the bot name  

---

### Required Interface

Each bot **must** implement:

```python
def play(state, rng):
    return Move.ROCK
```

- Must return a `Move` enum
- Never return strings

---

## 3. Determinism & Randomness

- RNG is fully deterministic
- Controlled by `SEED_SALT` in `config.py`
- Same inputs → same tournament results

---

## 4. COMPETITION Mode

```python
COMPETITION = True
```

- `False` → no files written
- `True` → results saved to `results/`

---

## 5. Results Layout

```
results/
└── tournament_<timestamp>/
    ├── metadata/
    ├── raw/
    │   └── rounds.jsonl
    └── leaderboard.csv
```

Do not delete `raw/` if you want replay validation.

---

## 6. Files Safe to Remove

- main.py
- engine/sandbox.py
- tests/test_replay_e2e.py

---

Chaos League values determinism over test scaffolding.
