
import unittest
import pandas as pd
import numpy as np
from src.strategy.optimization import Optimizer
from src.strategy.plugins.ma_strategy import MAStrategy

class TestOptimization(unittest.TestCase):
    def setUp(self):
        # Create dummy data with a trend
        dates = pd.date_range(start="2023-01-01", periods=200)
        # Generate a sine wave + trend
        close = [100 + i * 0.1 + 5 * np.sin(i / 10) for i in range(200)]

        data = {
            "date": dates,
            "open": close,
            "close": close,
            "high": [c + 1 for c in close],
            "low": [c - 1 for c in close],
            "volume": [1000] * 200
        }
        self.df = pd.DataFrame(data)

    def test_pso_optimization(self):
        optimizer = Optimizer("MA Strategy", self.df)

        # Define bounds for MA Strategy
        bounds = {
            "short_period": (2, 20, int),
            "long_period": (21, 100, int)
        }

        result = optimizer.optimize_pso(bounds, num_particles=10, max_iter=5)

        print("PSO Optimization Result:", result)
        self.assertIsNotNone(result["best_params"])
        self.assertIn("short_period", result["best_params"])
        self.assertIn("long_period", result["best_params"])
        # Ensure logic holds
        self.assertTrue(result["best_params"]["short_period"] <= 20)
        self.assertTrue(result["best_params"]["long_period"] >= 21)

if __name__ == "__main__":
    unittest.main()
