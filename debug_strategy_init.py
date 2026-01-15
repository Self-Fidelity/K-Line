
import sys
from pathlib import Path
sys.path.insert(0, str(Path("d:/K-Line")))

from src.strategy.manager import StrategyManager

print("Initializing StrategyManager...")
manager = StrategyManager()
print("Strategies loaded.")
