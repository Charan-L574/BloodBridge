"""
Background Training Scheduler
Runs periodic checks for model retraining in the background
"""

import asyncio
from datetime import datetime
from sqlmodel import Session
from database import engine
from adaptive_training import trigger_adaptive_training
import traceback


class BackgroundTrainingScheduler:
    """
    Background task that periodically checks if models need retraining
    """
    
    def __init__(self, check_interval_seconds: int = 3600):
        self.check_interval = check_interval_seconds  # Default 1 hour
        self.is_running = False
        self.task = None
    
    async def start(self):
        """Start the background scheduler"""
        if self.is_running:
            print("⚠️ Background training scheduler already running")
            return
        
        self.is_running = True
        print(f"🚀 Starting background training scheduler (checking every {self.check_interval//60} minutes)")
        
        self.task = asyncio.create_task(self._run())
    
    async def stop(self):
        """Stop the background scheduler"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("🛑 Background training scheduler stopped")
    
    async def _run(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.check_interval)
                
                if not self.is_running:
                    break
                
                print(f"\n⏰ [{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled ML training check...")
                
                # Run training check in a separate thread to avoid blocking
                with Session(engine) as session:
                    result = trigger_adaptive_training(session)
                    
                    if result.get("response_predictor", {}).get("retrained"):
                        print("✅ Response Predictor automatically retrained!")
                    
                    if result.get("demand_forecast", {}).get("retrained"):
                        print("✅ Demand Forecast automatically retrained!")
                    
                    if not result.get("response_predictor", {}).get("retrained") and not result.get("demand_forecast", {}).get("retrained"):
                        print("ℹ️ No retraining needed at this time")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in background training scheduler: {e}")
                traceback.print_exc()
                # Continue running even if there's an error
                await asyncio.sleep(60)  # Wait 1 minute before retrying


# Global scheduler instance
scheduler = BackgroundTrainingScheduler(check_interval_seconds=3600)  # Check every hour


async def start_background_training():
    """Start the background training scheduler"""
    await scheduler.start()


async def stop_background_training():
    """Stop the background training scheduler"""
    await scheduler.stop()
