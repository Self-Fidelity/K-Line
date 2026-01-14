from backend.app.services.strategy_service import StrategyService
from backend.app.services.strategy_manager import StrategyManager

def test_strategy_info():
    # Mocking necessary parts or just instantiating if possible
    # StrategyService needs StrategyManager
    # StrategyManager needs nothing usually, just imports plugins
    
    manager = StrategyManager()
    # Need to load strategies. StrategyManager.__init__ usually loads them?
    # Let's check StrategyManager
    # Assuming it loads from 'src/strategy/plugins'
    
    service = StrategyService()
    # service has .strategy_manager = StrategyManager()
    
    # List strategies to see what we have
    strategies = service.get_strategies()
    print("Available Strategies:", [s['name'] for s in strategies])
    
    for s in strategies:
        info = service.get_strategy_info(s['name'])
        print(f"\nInfo for {s['name']}:")
        print(f"Parameters: {info.get('parameters')}")
        print(f"Param Descs: {info.get('parameter_descriptions')}")

if __name__ == "__main__":
    test_strategy_info()
