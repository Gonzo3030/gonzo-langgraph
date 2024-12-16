#!/usr/bin/env python3

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from config.settings import load_config
from gonzo.core.agent import GonzoAgent
from gonzo.core.state import StateManager
from gonzo.evolution.system import EvolutionSystem
from gonzo.knowledge.graph import KnowledgeGraph
from gonzo.response.system import ResponseSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_environment() -> Dict[str, str]:
    """Initialize environment variables from .env file"""
    load_dotenv()
    required_vars = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'BRAVE_API_KEY',
        'LANGCHAIN_API_KEY',
        'CRYPTOCOMPARE_API_KEY',
        'YOUTUBE_API_KEY',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET'
    ]
    
    env_vars = {}
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f'Missing required environment variable: {var}')
        env_vars[var] = value
    
    # Optional vars with defaults
    env_vars['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2', 'true')
    env_vars['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
    env_vars['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT', 'gonzo-langgraph')
    
    return env_vars

def init_components(config: Dict[str, Any], env_vars: Dict[str, str]):
    """Initialize all system components"""
    # Initialize core components
    state_manager = StateManager()
    knowledge_graph = KnowledgeGraph()
    evolution_system = EvolutionSystem(state_manager)
    response_system = ResponseSystem(
        anthropic_key=env_vars['ANTHROPIC_API_KEY'],
        openai_key=env_vars['OPENAI_API_KEY'],
        brave_key=env_vars['BRAVE_API_KEY'],
        langchain_key=env_vars['LANGCHAIN_API_KEY'],
        cryptocompare_key=env_vars['CRYPTOCOMPARE_API_KEY'],
        x_credentials={
            'api_key': env_vars['X_API_KEY'],
            'api_secret': env_vars['X_API_SECRET'],
            'access_token': env_vars['X_ACCESS_TOKEN'],
            'access_secret': env_vars['X_ACCESS_SECRET']
        },
        youtube_key=env_vars['YOUTUBE_API_KEY']
    )
    
    # Initialize Gonzo agent
    agent = GonzoAgent(
        state_manager=state_manager,
        knowledge_graph=knowledge_graph,
        evolution_system=evolution_system,
        response_system=response_system,
        config=config
    )
    
    return agent

def health_check(agent: GonzoAgent) -> bool:
    """Perform basic health check of all components"""
    try:
        # Check each core component
        checks = [
            agent.state_manager.is_healthy(),
            agent.knowledge_graph.is_healthy(),
            agent.evolution_system.is_healthy(),
            agent.response_system.is_healthy()
        ]
        return all(checks)
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return False

def main():
    try:
        # Initialize environment and config
        env_vars = init_environment()
        config = load_config()
        
        # Initialize components
        agent = init_components(config, env_vars)
        
        # Perform health check
        if not health_check(agent):
            raise RuntimeError('System health check failed')
        
        # Start the main event loop
        logger.info('Starting Gonzo agent...')
        agent.run()
        
    except Exception as e:
        logger.error(f'Failed to start Gonzo: {str(e)}')
        raise

if __name__ == '__main__':
    main()
