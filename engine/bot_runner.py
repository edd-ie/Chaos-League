import time
from engine.judge import MOVES

DEFAULT_MOVE = MOVES[0]
TIMEOUT_SECONDS = 0.05


def safe_play(bot, state, rng):
    start = time.perf_counter()
    try:
        result = bot.play(state, rng)
    except Exception:
        return {"real_move": DEFAULT_MOVE}

    elapsed = time.perf_counter() - start
    if elapsed > TIMEOUT_SECONDS:
        return {"real_move": DEFAULT_MOVE}

    return result


def safe_shadow(bot, state):
    start = time.perf_counter()
    try:
        result = bot.request_shadow_move(state)
    except Exception:
        return False, None

    elapsed = time.perf_counter() - start
    if elapsed > TIMEOUT_SECONDS:
        return False, None

    return result
