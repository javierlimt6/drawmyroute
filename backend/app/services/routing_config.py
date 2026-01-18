"""
Routing Configuration - All tunable parameters in one place
"""

# === POINT SAMPLING ===
POINTS_DEFAULT = 80          # Default number of points to sample from SVG
POINTS_SUGGEST = 150         # More points for suggest (quality matters more)

# === SCALING ===
ROAD_DETOUR_FACTOR = 1.4     # Roads add ~40% to straight-line distance
SCALE_DAMPING = 0.6          # How aggressively to adjust scale (0-1)
SCALE_MIN = 0.3              # Minimum scale factor
SCALE_MAX = 2.5              # Maximum scale factor

# === ITERATIVE SCALING ===
MAX_ITERATIONS = 4           # Max attempts to hit target distance
TARGET_RATIO_MIN = 0.7       # Minimum acceptable distance ratio
TARGET_RATIO_MAX = 1.5       # Maximum acceptable distance ratio

# === QUALITY THRESHOLDS ===
MAX_FAILED_SEGMENT_RATIO = 0.25  # Reject if >25% segments fail routing
MIN_ACCEPTABLE_SCORE = 40.0      # Minimum score to accept a route

# === SCORING WEIGHTS ===
# Must sum to 1.0
SCORE_WEIGHT_DISTANCE = 0.40     # How close to target distance
SCORE_WEIGHT_COVERAGE = 0.40     # What % of route successfully routed
SCORE_WEIGHT_CLOSURE = 0.20      # How close start/end points are

# === OSRM ===
OSRM_MAX_CONCURRENT = 20         # Max parallel OSRM requests
OSRM_TIMEOUT_S = 10.0            # Timeout per OSRM request
DETOUR_THRESHOLD = 10.0          # Mark segment as outlier if >10x detour
MAX_SKIP_RATIO = 0.15            # Allow skipping up to 15% of waypoints
