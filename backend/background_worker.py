import time
from db_manager import get_latest_score

class BackgroundWorker:
    """Background worker for continuous data updates"""
    
    def __init__(self, settings, data_processor, signal_processor):
        self.settings = settings
        self.data_processor = data_processor
        self.signal_processor = signal_processor
    
    def check_and_populate_initial_data(self):
        """Check if database is empty and populate"""
        print(f"\n{'='*60}")
        print("Checking for initial data load...")
        print(f"{'='*60}")
        
        for symbol in self.settings['symbols']:
            latest_score = get_latest_score(symbol)
            if latest_score is None:
                print(f"  ⚠️  No scores for {symbol}. Loading initial data...")
                self.data_processor.update_symbol_data(symbol, historical_limit=200)
            else:
                print(f"  ✅ Existing scores found for {symbol}.")
        
        print(f"\n{'='*60}")
        print("Initial data load complete.")
        print(f"{'='*60}")
    
    def run(self):
        """Main background worker loop"""
        self.check_and_populate_initial_data()
        
        while True:
            try:
                for symbol in self.settings['symbols']:
                    master_score, weighted_indicators, interval_scores, current_price = \
                        self.data_processor.update_symbol_data(symbol)
                    
                    if all([master_score, weighted_indicators, interval_scores, current_price]):
                        self.signal_processor.process_trading_signals(
                            symbol, master_score, weighted_indicators,
                            interval_scores, current_price
                        )
                
                print("\n✅ Background worker finished update cycle")
            except Exception as e:
                print(f"❌ Error in background worker: {e}")
                import traceback
                traceback.print_exc()
            
            update_interval = self.settings['updateIntervalMinutes'] * 60
            print(f"\n⏰ Sleeping for {self.settings['updateIntervalMinutes']} minutes...")
            time.sleep(update_interval)

