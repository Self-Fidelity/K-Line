import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from src.strategy.plugins.bollinger_strategy import BollingerStrategy
    
    s = BollingerStrategy()
    info = s.get_strategy_info()
    print("Bollinger Strategy Info:", info)
    print("Parameters:", info.get('parameters'))
except Exception as e:
    print("Error:", e)
