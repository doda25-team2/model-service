"""
General configurations, variables and constant needed throughout the project.

Run script in isolation to receive some basic information about the settings.
"""
#stdlib
from pathlib import Path

# Path assignments:
ROOT = Path(__file__).parent.parent
TRAINING_DATA_PATH = ROOT / "smsspamcollection"
OUTPUT_PATH = ROOT / "output"

if __name__ == "__main__":
    print(f"{ROOT=}")
    print(f"{TRAINING_DATA_PATH=}")
