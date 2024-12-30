#!/usr/bin/env python3

import os
import sys
import signal
import asyncio
import logging
import subprocess
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GonzoSupervisor:
    def __init__(self):
        self.processes = {}
        self.running = False
        self._shutdown = False
    
    def start_process(self, name: str, script: str) -> subprocess.Popen:
        """Start a Python script as a subprocess."""
        if name in self.processes and self.processes[name].poll() is None:
            logger.warning(f"{name} is already running")
            return self.processes[name]
            
        process = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        self.processes[name] = process
        logger.info(f"Started {name} (PID: {process.pid})")
        return process
    
    def stop_process(self, name: str) -> None:
        """Stop a running process."""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                process.terminate()
                process.wait()
                logger.info(f"Stopped {name}")
            del self.processes[name]
    
    async def monitor_output(self, process: subprocess.Popen, name: str) -> None:
        """Monitor and log process output."""
        while True:
            if process.poll() is not None:
                break
                
            output = process.stdout.readline()
            if output:
                logger.info(f"{name}: {output.strip()}")
                
            error = process.stderr.readline()
            if error:
                logger.error(f"{name}: {error.strip()}")
                
            await asyncio.sleep(0.1)
    
    def is_run_time(self) -> bool:
        """Check if it's time to run the content generation workflow."""
        now = datetime.now()
        # Run at 6 AM, 2 PM, and 10 PM
        run_hours = [6, 14, 22]
        return now.hour in run_hours and now.minute == 0
    
    async def shutdown(self, sig=None):
        """Handle graceful shutdown."""
        if sig:
            logger.info(f'Received exit signal {sig.name}...')
        
        self._shutdown = True
        logger.info('Initiating graceful shutdown...')
        
        # Stop all processes
        for name in list(self.processes.keys()):
            self.stop_process(name)
        
        self.running = False
        logger.info('Shutdown complete')
    
    async def run(self):
        """Run the supervisor."""
        try:
            self.running = True
            self._shutdown = False
            
            # Setup signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                asyncio.get_event_loop().add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self.shutdown(s))
                )
            
            # Start publisher immediately
            publisher = self.start_process('publisher', 'run_publisher.py')
            monitor_task = asyncio.create_task(self.monitor_output(publisher, 'publisher'))
            
            logger.info('Starting Gonzo supervisor...')
            
            last_run = None
            while not self._shutdown:
                now = datetime.now()
                
                # Check if it's time to run content generation
                if self.is_run_time() and (not last_run or (now - last_run).seconds >= 3600):
                    logger.info('Starting content generation cycle')
                    gonzo = self.start_process('content_gen', 'run_gonzo.py')
                    await self.monitor_output(gonzo, 'content_gen')
                    last_run = now
                
                # Check process health
                if 'publisher' in self.processes and self.processes['publisher'].poll() is not None:
                    logger.warning('Publisher process died, restarting...')
                    self.stop_process('publisher')
                    publisher = self.start_process('publisher', 'run_publisher.py')
                    monitor_task.cancel()
                    monitor_task = asyncio.create_task(self.monitor_output(publisher, 'publisher'))
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f'Supervisor error: {str(e)}')
            raise
            
        finally:
            self.running = False
            monitor_task.cancel()

def run_supervisor():
    """Main execution function"""
    supervisor = GonzoSupervisor()
    asyncio.run(supervisor.run())

if __name__ == '__main__':
    run_supervisor()