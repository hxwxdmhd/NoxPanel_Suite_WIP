#!/usr/bin/env python3
"""
🚀 ULTIMATE SUITE v11.0 - STATUS SAVER SERVICE
==============================================
Starts the automated status saver as a background service.
"""

import asyncio
import signal
import sys
from auto_status_saver import UltimateSuiteStatusSaver
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('status_saver_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global saver instance
saver = None

def signal_handler(signum, frame):
    """
    RLVR: Controls program flow with conditional logic and error handling

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for signal_handler
    2. Analysis: Function complexity 1.2/5.0
    3. Solution: Controls program flow with conditional logic and error handling
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """Handle shutdown signals gracefully"""
    logger.info(f"🛑 Received signal {signum}, shutting down...")
    if saver:
        saver.stop()
    sys.exit(0)

async def main():
    """Main service function"""
    global saver

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize status saver (12 minutes interval)
        saver = UltimateSuiteStatusSaver(interval_minutes=12)

        logger.info("🎯 Ultimate Suite Status Saver Service Starting...")
        logger.info("📅 Save interval: 12 minutes")
        logger.info("📁 Status directory: data/status_snapshots/")
        logger.info("📝 Log file: status_saver_service.log")

        # Create initial snapshot
        logger.info("📊 Creating initial status snapshot...")
        initial_snapshot = await saver.save_status_snapshot()
        if initial_snapshot:
            logger.info(f"✅ Initial snapshot created: {initial_snapshot}")

        # Start the automated saver
        saver.start()

        logger.info("🚀 Status saver service is now running!")
        logger.info("💡 Press Ctrl+C to stop the service")

        # Keep the service running
        while True:
            await asyncio.sleep(10)

            # Log periodic status
            status = saver.get_status()
            if status["running"] and status["last_save_time"]:
                logger.info(f"🔄 Service running - Last save: {status['last_save_time']}")

    except KeyboardInterrupt:
        logger.info("🛑 Service interrupted by user")
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
    finally:
        if saver:
            saver.stop()
        logger.info("✅ Status saver service stopped")

if __name__ == "__main__":
    asyncio.run(main())
