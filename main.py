import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator import run_pipeline

if __name__ == "__main__":
    print("Starting Swing Trading Assistant...")
    final = run_pipeline()