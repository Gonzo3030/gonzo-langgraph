# Updated Gonzo Architecture

```mermaid
graph TB
    %% Core State Management
    State[UnifiedState] --> MarketData
    State --> SocialData
    State --> NewsData
    State --> Analysis
    State --> Memory
    
    %% Monitoring Components
    subgraph Monitoring
        MarketMonitor[Market Monitor Node] --> CryptoAPI[CryptoCompare API]
        NewsMonitor[News Monitor Node] --> BraveAPI[Brave Search API]
        SocialMonitor[Social Monitor Node] --> XIntegration[X API]
    end
    
    %% Analysis Components
    subgraph Analysis Flow
        PatternAnalysis[Pattern Analysis Node]
        NarrativeGen[Narrative Generation Node]
        CausalAnalyzer[Causal Analyzer]
    end
    
    %% Response Components
    subgraph Response
        ResponsePost[Response Posting Node]
        XQueue[X Post Queue]
    end
    
    %% Error Handling
    ErrorRecovery[Error Recovery Node]
    
    %% Data Flow
    MarketMonitor --> |Market Data| State
    NewsMonitor --> |News Events| State
    SocialMonitor --> |Social Data| State
    
    State --> PatternAnalysis
    PatternAnalysis --> |Patterns| State
    PatternAnalysis --> |Significant Patterns| NarrativeGen
    
    NarrativeGen --> |Generated Content| State
    NarrativeGen --> |High Significance| ResponsePost
    
    %% Error Handling Flow
    MarketMonitor --> |Errors| ErrorRecovery
    NewsMonitor --> |Errors| ErrorRecovery
    SocialMonitor --> |Errors| ErrorRecovery
    PatternAnalysis --> |Errors| ErrorRecovery
    NarrativeGen --> |Errors| ErrorRecovery
    ResponsePost --> |Errors| ErrorRecovery
    
    ErrorRecovery --> |Recovery| MarketMonitor
    
    %% Cycle Flow
    ResponsePost --> |Next Cycle| MarketMonitor
    
    %% Style Definitions
    classDef state fill:#2374ab,stroke:#2374ab,stroke-width:2px,color:#fff
    classDef monitoring fill:#048ba8,stroke:#048ba8,stroke-width:2px,color:#fff
    classDef analysis fill:#0db39e,stroke:#0db39e,stroke-width:2px,color:#fff
    classDef response fill:#16db93,stroke:#16db93,stroke-width:2px,color:#fff
    classDef error fill:#f94144,stroke:#f94144,stroke-width:2px,color:#fff
    classDef api fill:#f8961e,stroke:#f8961e,stroke-width:2px,color:#fff
    
    %% Apply Styles
    class State,MarketData,SocialData,NewsData,Analysis,Memory state
    class MarketMonitor,NewsMonitor,SocialMonitor monitoring
    class PatternAnalysis,NarrativeGen,CausalAnalyzer analysis
    class ResponsePost,XQueue response
    class ErrorRecovery error
    class CryptoAPI,BraveAPI,XIntegration api
```

## Workflow Stages

1. **Market Monitoring**
   - Fetches current crypto market data
   - Detects significant price movements
   - Updates state with market events

2. **News Monitoring** (Every 5 cycles)
   - Searches for relevant crypto news
   - Focuses on whale movements and manipulation
   - Updates state with significant news events

3. **Social Monitoring**
   - Monitors X for relevant discussions
   - Handles rate limiting
   - Tracks influencer activity

4. **Pattern Analysis**
   - Analyzes market, news, and social data
   - Detects significant patterns
   - Identifies correlations

5. **Narrative Generation**
   - Generates Gonzo's perspective
   - Creates thread suggestions
   - Determines response significance

6. **Response Posting**
   - Posts high-significance narratives
   - Manages X API interactions
   - Updates state with post status

7. **Error Recovery**
   - Handles component failures
   - Logs errors
   - Attempts graceful recovery