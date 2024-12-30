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
            
        try:
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            self.processes[name] = process
            logger.info(f"Started {name} (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {str(e)}")
            return None
    
    def stop_process(self, name: str) -> None:
        """Stop a running process."""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                logger.info(f"Stopped {name}")
            del self.processes[name]
    
    async def monitor_output(self, process: subprocess.Popen, name: str) -> None:
        """Monitor and log process output."""
        async def read_stream(stream, prefix):
            while True:
                line = stream.readline()
                if not line:
                    break
                if prefix == 'ERROR':
                    logger.error(f"{name}: {line.strip()}")
                else:
                    logger.info(f"{name}: {line.strip()}")

        try:
            await asyncio.gather(
                asyncio.create_task(read_stream(process.stdout, 'OUT')),
                asyncio.create_task(read_stream(process.stderr, 'ERROR'))
            )
        except Exception as e:
            logger.error(f"Error monitoring {name}: {str(e)}")
    
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
    
    async def run_content_generation(self) -> None:
        """Run the content generation workflow and wait for completion."""
        logger.info('Starting content generation cycle')
        gonzo = self.start_process('content_gen', 'run_gonzo.py')
        if gonzo:
            await self.monitor_output(gonzo, 'content_gen')
            return_code = gonzo.wait()
            logger.info(f'Content generation completed with code {return_code}')
    
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
            
            logger.info('Starting Gonzo supervisor...')
            
            # Run content generation immediately
            await self.run_content_generation()
            
            # Start publisher
            publisher = self.start_process('publisher', 'run_publisher.py')
            if publisher:
                monitor_task = asyncio.create_task(self.monitor_output(publisher, 'publisher'))
            
            last_run = datetime.now()
            while not self._shutdown:
                now = datetime.now()
                
                # Check if it's time to run content generation
                if self.is_run_time() and (now - last_run).seconds >= 3600:
                    await self.run_content_generation()
                    last_run = now
                
                # Check publisher health
                if publisher and publisher.poll() is not None:
                    logger.warning('Publisher process died, restarting...')
                    self.stop_process('publisher')
                    publisher = self.start_process('publisher', 'run_publisher.py')
                    if publisher:
                        monitor_task.cancel()
                        monitor_task = asyncio.create_task(self.monitor_output(publisher, 'publisher'))
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f'Supervisor error: {str(e)}')
            raise
            
        finally:
            self.running = False
            if 'monitor_task' in locals():
                monitor_task.cancel()

def run_supervisor():
    """Main execution function"""
    supervisor = GonzoSupervisor()
    asyncio.run(supervisor.run())

if __name__ == '__main__':
    run_supervisor()