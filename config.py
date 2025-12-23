# config.py

# ----- Window / world -----
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540

BACKGROUND_COLOR = (230, 230, 230)
DRIVEABLE_COLOR = (255, 255, 255)
WALL_COLOR = (120, 120, 120)
CHECKPOINT_COLOR = (50, 120, 255)
START_COLOR = (0, 200, 0)
CAR_COLOR = (220, 40, 40)

CELL = 30  # just for designing tracks if you want

FPS = 60
DT = 0.18  # simulation time step for each gene

# ----- Car physics -----
MAX_SPEED = 7.0
ACCEL = 3.0
FRICTION = 0.15
TURN_RATE = 2.4  # radians/s when steer=1

CAR_WIDTH = 18
CAR_LENGTH = 10

# ----- GA parameters -----
POP_SIZE = 80
ELITE_COUNT = 5
PARENT_POOL = 20
MUTATION_RATE = 0.10
MUTATION_STD = 0.4  # stddev for steering/throttle mutation

BASE_GENOME_LEN = 30
GENOME_INC = 6      # add this many steps when we grow
GENS_PER_INC = 6    # grow every N generations

# ----- Project paths -----
TRACK_DIR = "tracks"
SAVE_DIR = "saves"

# ----- Replay / UI -----
AUTO_REPLAY = True        # auto show best every generation
REPLAY_FPS = 60
CHART_WIDTH = 260
CHART_HEIGHT = 110
