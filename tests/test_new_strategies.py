
import unittest
import pandas as pd
from src.strategy.plugins.kdj_strategy import KDJStrategy
from src.strategy.plugins.turtle_strategy import TurtleStrategy
from src.strategy.plugins.vwma_strategy import VWMAStrategy

class TestNewStrategies(unittest.TestCase):
    def setUp(self):
        # Create dummy data
        dates = pd.date_range(start="2023-01-01", periods=100)
        data = {
            "date": dates,
            "open": [100 + i * 0.1 for i in range(100)],
            "close": [100 + i * 0.2 + (i % 5) for i in range(100)],
            "high": [105 + i * 0.2 for i in range(100)],
            "low": [95 + i * 0.2 for i in range(100)],
            "volume": [1000 + i * 10 for i in range(100)]
        }
        self.df = pd.DataFrame(data)

    def test_kdj(self):
        strategy = KDJStrategy()
        result = strategy.analyze(self.df)
        self.assertIn("k", result.columns)
        self.assertIn("d", result.columns)
        self.assertIn("j", result.columns)
        self.assertIn("signal", result.columns)

    def test_turtle(self):
        strategy = TurtleStrategy(entry_period=5, exit_period=3)
        result = strategy.analyze(self.df)
        self.assertIn("donchian_high", result.columns)
        self.assertIn("signal", result.columns)

    def test_vwma(self):
        strategy = VWMAStrategy(short_period=5, long_period=10)
        result = strategy.analyze(self.df)
        self.assertIn("vwma_short", result.columns)
        self.assertIn("signal", result.columns)

if __name__ == "__main__":
    unittest.main()
