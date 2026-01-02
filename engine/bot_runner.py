import multiprocessing
from engine.judge import MOVES

DEFAULT_MOVE = MOVES[0]  # fallback if bot times out or crashes
TIMEOUT_SECONDS = 0.05   # 50ms per move

def safe_play(bot_class, state, rng):
    """
    Runs bot.play() with a timeout in a subprocess.
    Returns a dict with 'real_move' and optional 'shadow'.
    """
    def target(queue):
        try:
            result = bot_class.play(state, rng)
            queue.put(result)
        except Exception as e:
            queue.put({"real_move": DEFAULT_MOVE})

    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=target, args=(queue,))
    p.start()
    p.join(TIMEOUT_SECONDS)
    if p.is_alive():
        p.terminate()
        return {"real_move": DEFAULT_MOVE}
    if queue.empty():
        return {"real_move": DEFAULT_MOVE}
    return queue.get()


def safe_shadow(bot_class, state):
    """
    Runs bot.request_shadow_move() with a timeout.
    Returns (False, None) if timeout occurs.
    """
    def target(queue):
        try:
            result = bot_class.request_shadow_move(state)
            queue.put(result)
        except Exception:
            queue.put((False, None))

    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=target, args=(queue,))
    p.start()
    p.join(TIMEOUT_SECONDS)
    if p.is_alive():
        p.terminate()
        return False, None
    if queue.empty():
        return False, None
    return queue.get()
