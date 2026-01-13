
import unittest
import os
import json
import sqlite3
from src.data_storage.sqlite_storage import SQLiteStorage

class TestSQLiteStorageParams(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_params.db"
        self.storage = SQLiteStorage(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_get_params(self):
        stock_code = "000001"
        strategy_name = "MA Strategy"
        params = {"short_period": 5, "long_period": 20}
        params_str = json.dumps(params)

        self.storage.save_strategy_params(stock_code, strategy_name, params_str)

        loaded_params_str = self.storage.get_strategy_params(stock_code, strategy_name)
        self.assertIsNotNone(loaded_params_str)

        loaded_params = json.loads(loaded_params_str)
        self.assertEqual(loaded_params, params)

        # Test update
        new_params = {"short_period": 10, "long_period": 30}
        new_params_str = json.dumps(new_params)
        self.storage.save_strategy_params(stock_code, strategy_name, new_params_str)

        loaded_params_str = self.storage.get_strategy_params(stock_code, strategy_name)
        loaded_params = json.loads(loaded_params_str)
        self.assertEqual(loaded_params, new_params)

if __name__ == "__main__":
    unittest.main()
