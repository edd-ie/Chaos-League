"""
Spot-Check Chaos League Replay Test

Purpose:
- Validate determinism for a single match from latest tournament logs
- Ensures Move enums match logged moves
- Minimal maintenance, safe for evolving bots
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

    # pick just the first replay metadata file as a spot check
    # We filter for bot-specific match files if they exist, 
    # otherwise we use the tournament metadata.
    replay_files = sorted(metadata_dir.glob("replay_*.json"))
    if not replay_files:
        # Fallback: check if we can use the tournament.json if it contains match info
        tournament_json = metadata_dir / "tournament.json"
        if tournament_json.exists():
            replay_files = [tournament_json]
        else:
            raise RuntimeError(f"No replay metadata files found in {metadata_dir}")

    replay_meta_path = replay_files[0]
    print(f"Validating spot-check replay: {replay_meta_path.name}...\n")

    try:
        validate_match_replay(replay_meta_path, BOTS_DIR)
    except Exception as e:
        print(f"[ERROR] Replay validation failed: {e}")
        raise

    print("\nSpot-check replay validated successfully!")


if __name__ == "__main__":
    main()
