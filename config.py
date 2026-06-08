# config.py

# ----- Window / world -----
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540

BACKGROUND_COLOR = (195, 200, 215)    # off-track: cool light gray
DRIVEABLE_COLOR  = (235, 238, 248)    # road surface: near-white
WALL_COLOR       = (55, 58, 90)       # walls: dark slate
ROAD_EDGE_COLOR  = (170, 175, 195)    # road boundary line
CHECKPOINT_COLOR = (50, 100, 230)     # inactive ring
START_COLOR      = (0, 190, 100)
CAR_COLOR        = (0, 160, 230)      # electric blue

CELL = 30

FPS = 60
DT = 0.18

# ----- Car physics -----
MAX_SPEED = 7.0
ACCEL = 3.0
FRICTION = 0.15
TURN_RATE = 2.4  # radians/s when steer=1

CAR_WIDTH = 18
CAR_LENGTH = 10

# ----- Raycasts -----
RAY_ANGLES = [-90, -60, -30, 0, 30, 60, 90]  # degrees relative to heading
MAX_RAY_DIST = 300.0

# ----- Neural network -----
NN_INPUTS = len(RAY_ANGLES) + 1  # rays + normalised speed
NN_HIDDEN = 10
NN_OUTPUTS = 2  # steer, throttle
GENOME_LEN = NN_INPUTS * NN_HIDDEN + NN_HIDDEN + NN_HIDDEN * NN_OUTPUTS + NN_OUTPUTS

# ----- Simulation -----
SIM_STEPS = 700  # max steps per genome evaluation

# ----- GA parameters -----
POP_SIZE = 80
ELITE_COUNT = 5
PARENT_POOL = 20
MUTATION_RATE = 0.12
MUTATION_STD = 0.25

# ----- Project paths -----
TRACK_DIR = "tracks"
SAVE_DIR = "saves"

# ----- UI -----
REPLAY_FPS = 60
CHART_WIDTH  = 240
CHART_HEIGHT = 100
