from typing import Dict, Tuple

import os

# Base directory relative to this file or from env
BASE_DIR = os.getenv("GOINSIGHT_BASE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
MODEL_DIR = os.getenv("KATAGO_MODEL_DIR", os.path.join(BASE_DIR, "model"))
CONFIG_DIR = os.getenv("KATAGO_CONFIG_DIR", os.path.join(BASE_DIR, "configs"))
NEURALNET_DIR = os.getenv("KATAGO_NEURALNET_DIR", os.path.join(BASE_DIR, "neuralnet"))

ANALYSIS_CONFIG_PATH = os.path.join(MODEL_DIR, "analysis_example.cfg")
GAME_ANALYSIS_CONFIG_PATH = os.path.join(CONFIG_DIR, "fast_game_analysis.cfg")
TURN_ANALYSIS_CONFIG_PATH = os.path.join(CONFIG_DIR, "deep_analysis.cfg")

NEURALNET_PATH = os.path.join(NEURALNET_DIR, "g170e-b10c128-s1141046784-d204142634.bin.gz")

# Lower and upper bounds of winrate loss for each move classification
MOVE_CLASSIFICATION_BOUNDS: Dict[str, Tuple[int, int]] = {
    "BEST": (-1.0, -0.55),        # 5th percentile of winrate loss
    "EXCELLENT": (-0.55, -0.2),   # 27.5th percentile of winrate loss
    "GOOD": (-0.2, -0.02),        # 50th percentile of winrate loss
    "INACCURACY": (-0.02, 0.002), # 85th percentile of winrate loss
    "MISTAKE": (0.002, 0.01),     # 95th percentile of winrate loss
    "BLUNDER": (0.01, 1.0)        # Above the 95th percentile of winrate loss
    }

# Amount of move proposition given by the deep turn analysis
MOVE_PROPOSITIONS_PER_TURN = 3

# Maximum amount of move given in the possible variation for a move
PV_MAX_LENGTH = 5
