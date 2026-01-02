"""
End-to-end Chaos League determinism test.

Runs:
1) Match execution (competition mode)
2) Log generation
3) Replay validation

Works even if only one bot exists,
by pairing it with the reference bot.
"""

import pathlib
import json

from engine.match import run_match
from engine.logger import init_logging, finalize_logging, log_match_summary
from engine.bot_loader import load_bot
from engine.replay_validator import validate_match_replay

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
BOTS_DIR = PROJECT_ROOT / "bots"
REFERENCE_BOT = "reference_bot"



def main():
    bots = sorted(p.stem for p in BOTS_DIR.glob("*.py") if p.stem != "__init__")

    if not bots:
        raise RuntimeError("No bots found in bots/")

    # Use first bot vs reference
    bot_name = bots[0]

    bot_a = load_bot(BOTS_DIR / f"{bot_name}.py")
    bot_b = load_bot(BOTS_DIR / f"{REFERENCE_BOT}.py")

    init_logging(competition=True)

    summary = run_match(
        bot_a,
        bot_b,
        name_a=bot_name,
        name_b=REFERENCE_BOT,
    )

    log_match_summary(summary)
    finalize_logging()

    # --- Build replay metadata ---
    results_root = sorted(pathlib.Path("results").glob("tournament_*"))[-1]
    rounds_log = results_root / "raw" / "rounds.jsonl"

    replay_meta = {
        "bot_a": bot_name,
        "bot_b": REFERENCE_BOT,
        "rounds_log": str(rounds_log),
    }

    meta_path = results_root / "metadata" / "replay_test.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(replay_meta, f, indent=2)

    # --- Replay validation ---
    validate_match_replay(meta_path, BOTS_DIR)


if __name__ == "__main__":
    main()
