from typing import Dict, List, Any, Optional
from datetime import datetime, UTC
import json
from pathlib import Path

class ContentMemoryManager:
    """Manages historical content and context for the evolution system"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path('memory')
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def store_content(self,
                           content_type: str,
                           entities: List[Dict[str, Any]],
                           patterns: List[Dict[str, Any]],
                           timestamp: datetime,
                           segments: Optional[List[Dict[str, Any]]] = None):
        """Store processed content with metadata"""
        content_data = {
            'type': content_type,
            'timestamp': timestamp.isoformat(),
            'entities': entities,
            'patterns': patterns
        }
        
        if segments:
            content_data['segments'] = segments
        
        # Store in date-based directory structure
        date_path = self.storage_path / timestamp.strftime('%Y/%m/%d')
        date_path.mkdir(parents=True, exist_ok=True)
        
        # Use timestamp as unique identifier
        file_path = date_path / f'{timestamp.strftime("%H%M%S")}.json'
        
        with open(file_path, 'w') as f:
            json.dump(content_data, f, indent=2)
            
    async def get_historical_context(self, 
                                    days_back: int = 7,
                                    content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve historical content for context"""
        context = []
        current = datetime.now(UTC)
        
        try:
            # Iterate through recent days
            for day in range(days_back):
                date_path = self.storage_path / current.strftime('%Y/%m/%d')
                if date_path.exists():
                    for file_path in date_path.glob('*.json'):
                        try:
                            with open(file_path) as f:
                                data = json.load(f)
                                if not content_type or data['type'] == content_type:
                                    context.append(data)
                        except (json.JSONDecodeError, IOError) as e:
                            continue  # Skip problematic files
                            
            return sorted(context, key=lambda x: x['timestamp'])
            
        except Exception:
            return []  # Return empty list if anything goes wrong