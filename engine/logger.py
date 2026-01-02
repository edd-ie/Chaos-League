"""
Logging system for Chaos League.
"""

import json
import pathlib
import hashlib
from datetime import datetime, timezone

import config
from engine.judge import Move

_RESULTS_ROOT = None
_RAW_FILE = None
_SUMMARY_FILE = None
_METADATA_PATH = None
_COMPETITION = False


# -------------------------------
# Helpers
# -------------------------------

def _config_fingerprint():
    payload = {
        "ROUNDS": config.ROUNDS,
        "DECEPTION_TOKENS": config.DECEPTION_TOKENS,
        "SEED_SALT": config.SEED_SALT,
        "SHADOW_REJECT_PROB": config.SHADOW_REJECT_PROB,
    }
    blob = json.dumps(payload, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:10]


def _timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ensure_dir(path: pathlib.Path):
    path.mkdir(parents=True, exist_ok=True)


def _serialize(obj):
    if isinstance(obj, Move):
        return obj.name
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


# -------------------------------
# Public API
# -------------------------------

def init_logging(competition: bool):
    global _RESULTS_ROOT, _RAW_FILE, _SUMMARY_FILE, _METADATA_PATH, _COMPETITION

    _COMPETITION = competition
    if not _COMPETITION:
        return

    fingerprint = _config_fingerprint()
    stamp = _timestamp()

    _RESULTS_ROOT = pathlib.Path("results") / f"tournament_{stamp}_{fingerprint}"
    raw_dir = _RESULTS_ROOT / "raw"
    summary_dir = _RESULTS_ROOT / "summaries"
    meta_dir = _RESULTS_ROOT / "metadata"

    _ensure_dir(raw_dir)
    _ensure_dir(summary_dir)
    _ensure_dir(meta_dir)

    if config.LOG_RAW_DATA:
        _RAW_FILE = open(raw_dir / "rounds.jsonl", "w", encoding="utf-8")

    if config.LOG_SUMMARIES:
        _SUMMARY_FILE = open(summary_dir / "matches.jsonl", "w", encoding="utf-8")

    _METADATA_PATH = meta_dir / "tournament.json"

    metadata = {
        "timestamp_utc": stamp,
        "engine_version": config.ENGINE_VERSION,
        "config": {
            "ROUNDS": config.ROUNDS,
            "DECEPTION_TOKENS": config.DECEPTION_TOKENS,
            "SHADOW_REJECT_PROB": config.SHADOW_REJECT_PROB,
            "SEED_SALT": config.SEED_SALT,
        },
        "config_fingerprint": fingerprint,
    }

    with open(_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def log_round(data: dict):
    if not (_COMPETITION and _RAW_FILE):
        return

    _RAW_FILE.write(json.dumps(_serialize(data)) + "\n")


def log_match_summary(summary: dict):
    if not (_COMPETITION and _SUMMARY_FILE):
        return

    _SUMMARY_FILE.write(json.dumps(_serialize(summary)) + "\n")


def log_metadata(extra: dict):
    if not _COMPETITION:
        return

    with open(_METADATA_PATH, "r+", encoding="utf-8") as f:
        metadata = json.load(f)
        metadata.update(_serialize(extra))
        f.seek(0)
        json.dump(metadata, f, indent=2)
        f.truncate()


def finalize_logging():
    for f in (_RAW_FILE, _SUMMARY_FILE):
        if f:
            f.flush()
            f.close()
