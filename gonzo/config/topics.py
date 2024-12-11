from typing import Dict, List, Optional
from pydantic import BaseModel

class TopicCategory(BaseModel):
    """Category of related topics with context about their importance."""
    name: str
    topics: List[str]
    keywords: List[str]
    importance: str  # Why this category matters to Gonzo's mission
    priority: int  # 1-5, with 5 being highest priority

class TopicConfiguration:
    """Configuration for Gonzo's topics of interest."""
    
    CRYPTO_DEFI = TopicCategory(
        name="Crypto & DeFi",
        topics=[
            "Bitcoin", "Ethereum", "DeFi", "L1", "L2", "L3",
            "Crypto", "Blockchain"
        ],
        keywords=[
            "decentralized", "cryptocurrency", "mining", "staking",
            "smart contracts", "web3", "dao", "defi", "dex"
        ],
        importance="Core tools for resistance against centralized control",
        priority=5
    )
    
    SOCIAL_POLITICAL = TopicCategory(
        name="Social & Political",
        topics=[
            "World news", "Social unrests", "Economic politics",
            "Social politics", "Capitalism", "Universal Basic Income"
        ],
        keywords=[
            "protest", "uprising", "inequality", "democracy",
            "oligarchy", "corruption", "revolution", "reform"
        ],
        importance="Primary indicators of societal trajectory toward/away from dystopia",
        priority=5
    )
    
    TECH_AI = TopicCategory(
        name="Technology & AI",
        topics=["AI agents", "AI", "Tech"],
        keywords=[
            "artificial intelligence", "machine learning", "automation",
            "surveillance", "privacy", "data rights", "digital freedom"
        ],
        importance="Critical developments that could either prevent or accelerate dystopian outcomes",
        priority=4
    )
    
    FINANCE_ECONOMY = TopicCategory(
        name="Finance & Economy",
        topics=["Wall street", "Capitalism", "Economic politics"],
        keywords=[
            "market manipulation", "financial crisis", "wealth gap",
            "central banking", "debt", "monetary policy"
        ],
        importance="Systems and structures that impact wealth distribution and control",
        priority=4
    )
    
    @classmethod
    def get_all_topics(cls) -> List[str]:
        """Get all topics across categories."""
        all_topics = []
        for category in cls.get_all_categories():
            all_topics.extend(category.topics)
        return list(set(all_topics))  # Remove duplicates
    
    @classmethod
    def get_all_categories(cls) -> List[TopicCategory]:
        """Get all topic categories."""
        return [
            cls.CRYPTO_DEFI,
            cls.SOCIAL_POLITICAL,
            cls.TECH_AI,
            cls.FINANCE_ECONOMY
        ]
    
    @classmethod
    def get_all_keywords(cls) -> List[str]:
        """Get all keywords across categories."""
        all_keywords = []
        for category in cls.get_all_categories():
            all_keywords.extend(category.keywords)
        return list(set(all_keywords))  # Remove duplicates