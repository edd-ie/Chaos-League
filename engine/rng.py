"""
RNG control and determinism enforcement for Chaos League.

This module guarantees:
- External seeding per match
- Deterministic replay
- No hidden entropy sources
"""

import random
import hashlib
import inspect

from config import SEED_SALT


# -------------------------------
# RNG Creation
# -------------------------------

def make_rng(name_a: str, name_b: str):
    """
    Creates two deterministic RNG instances for a match.
    One RNG per bot, derived from the same match seed.
    """

    seed_str = f"{name_a}|{name_b}|{SEED_SALT}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**32)

    rng_a = random.Random(seed ^ 0xA5A5A5A5)
    rng_b = random.Random(seed ^ 0x5A5A5A5A)

    return rng_a, rng_b


# -------------------------------
# RNG Compliance Enforcement
# -------------------------------

def verify_rng_compliance(bot_module, bot_name: str):
    """
    Performs a best-effort static inspection to detect
    illegal RNG usage inside a bot module.

    This is not a sandbox — it is a deterrent.
    """

    source = inspect.getsource(bot_module)

    banned_patterns = [
        "random.",
        "import random",
        "from random",
        "numpy.random",
        "np.random",
        "time.time",
        "os.urandom",
        "secrets.",
    ]

    violations = [
        pattern for pattern in banned_patterns
        if pattern in source
    ]

    if violations:
        raise RuntimeError(
            f"Bot '{bot_name}' violates RNG rules. "
            f"Illegal randomness detected: {violations}"
        )
