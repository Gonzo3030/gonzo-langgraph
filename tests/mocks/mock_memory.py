from typing import Dict, Any, List
from datetime import datetime
from gonzo.memory.interfaces import MemoryInterface, TimelineMemory

class MockMemoryInterface(MemoryInterface):
    """Mock memory interface for testing."""
    
    def __init__(self):
        self.memories = {
            "pre_1974": [
                TimelineMemory(
                    content="First encountered bitcoin's spiritual predecessor in a fevered dream at the Circus-Circus, 1971. "  
                           "Digital tokens exchanged for truth in a casino run by the technological-industrial complex.",
                    timestamp=datetime(1971, 5, 15),
                    category="crypto",
                    metadata={"location": "Las Vegas"}
                )
            ],
            "dark_period": [
                TimelineMemory(
                    content="Watched from the shadows as Satoshi released the whitepaper. Knew immediately it would "  
                           "become a tool for both liberation and control.",
                    timestamp=datetime(2008, 10, 31),
                    category="crypto",
                    metadata={"event": "Bitcoin whitepaper"}
                )
            ],
            "future": [
                TimelineMemory(
                    content="2027: The Great Crypto Schism. When they forced everyone into CBDCs, the resistance "  
                           "moved to truly decentralized systems. Blood in the digital streets.",
                    timestamp=datetime(2027, 3, 15),
                    category="crypto",
                    metadata={"event": "CBDC enforcement"}
                )
            ]
        }
        self.stored_memories = []
    
    async def get_relevant_memories(
        self,
        query: str,
        category: str,
        timeline: str,
        limit: int = 5
    ) -> List[TimelineMemory]:
        """Return mock memories for the given timeline."""
        return self.memories.get(timeline, [])
    
    async def store_memory(
        self,
        memory: TimelineMemory
    ) -> bool:
        """Store a mock memory."""
        self.stored_memories.append(memory)
        return True
    
    async def get_timeline_summary(
        self,
        category: str,
        timeline: str
    ) -> str:
        """Return a mock summary."""
        return f"Mock summary for {timeline} {category}"
    
    def get_stored_memories(self) -> List[TimelineMemory]:
        """Helper method to verify stored memories in tests."""
        return self.stored_memories