"""
Secure Bot Loader for Chaos League

Responsibilities:
- Load bot modules from disk
- Enforce interface compliance
- Enforce RNG usage rules (static inspection)
"""

import importlib.util
import inspect
import pathlib

from engine.rng import verify_rng_compliance


def load_bot(path: pathlib.Path):
    if not path.exists():
        raise RuntimeError(f"Bot file not found: {path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # --- Static RNG enforcement ---
    verify_rng_compliance(module, path.stem)

    # --- Interface enforcement ---
    if not hasattr(module, "Bot"):
        raise RuntimeError(f"Bot '{path.name}' missing required class 'Bot'")

    BotClass = module.Bot

    if not inspect.isclass(BotClass):
        raise RuntimeError(f"'Bot' in {path.name} is not a class")

    if not hasattr(BotClass, "play"):
        raise RuntimeError(f"Bot '{path.name}' missing method 'play'")

    if not callable(BotClass.play):
        raise RuntimeError(f"'play' in {path.name} is not callable")

    # --- Instantiate bot ---
    try:
        bot = BotClass()
    except Exception as e:
        raise RuntimeError(f"Bot '{path.name}' failed to initialize: {e}")

    return bot
