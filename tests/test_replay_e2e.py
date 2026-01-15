"""
End-to-end Chaos League replay test.

Purpose:
- Automatically replays all matches from the latest tournament logs
- Validates that every bot pair reproduces the same moves
- Guarantees Move enum consistency
- Works even if only one bot exists
"""

import pathlib
import json
from engine.replay_validator import validate_match_replay

RESULTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "results"
BOTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "bots"


def find_latest_tournament() -> pathlib.Path:
    tournaments = sorted(RESULTS_DIR.glob("tournament_*"))
    if not tournaments:
        raise RuntimeError("No tournament results found in 'results/'")
    return tournaments[-1]


def main():
    latest_tournament = find_latest_tournament()
    metadata_dir = latest_tournament / "metadata"

    replay_files = list(metadata_dir.glob("replay_*.json"))
    if not replay_files:
        raise RuntimeError(f"No replay metadata files found in {metadata_dir}")

    print(f"Validating {len(replay_files)} match replays from {latest_tournament.name}...\n")

    for replay_meta_path in replay_files:
        try:
            validate_match_replay(replay_meta_path, BOTS_DIR)
        except Exception as e:
            print(f"[ERROR] Replay validation failed for {replay_meta_path.name}: {e}")
            raise

    print("\nAll replays validated successfully!")


if __name__ == "__main__":
    main()
