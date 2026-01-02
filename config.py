# config.py

# ---- Runtime Mode ----
COMPETITION = True   # False = simulation, True = official run

# ---- Match Parameters ----
ROUNDS = 10_000
DECEPTION_TOKENS = 50
SHADOW_REJECT_PROB = 0.10

MATCHES_PER_PAIR = 3           # number of matches per bot pair

# ---- Determinism ----
SEED_SALT = "CHAOS_LEAGUE_2026"

# ---- Logging Controls ----
LOG_RAW_DATA = True
LOG_SUMMARIES = True

# Number of matches after which to print a leaderboard snapshot
LEADERBOARD_SNAPSHOT_INTERVAL = 10


# ---- Engine Metadata ----
ENGINE_VERSION = "0.1.2"
