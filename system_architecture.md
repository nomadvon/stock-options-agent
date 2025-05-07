# Trading Agent System Architecture

```mermaid
graph TB
    subgraph "Market Hours Management"
        MH[Market Hours Check]
        MH -->|Market Open| PO[Price Monitor]
        MH -->|Market Closed| Sleep[Sleep Until Open]
    end

    subgraph "24/7 Components"
        NM[News Monitor]
        EQ[Event Queue]
        EP[Event Processor]
    end

    subgraph "Market Hours Components"
        PO -->|Price Updates| EQ
        SG[Signal Generator]
        TA[Trading Agent]
    end

    subgraph "External Services"
        Alpaca[Alpaca API]
        Discord[Discord Webhook]
    end

    subgraph "Data Flow"
        NM -->|News Updates| EQ
        EQ -->|Events| EP
        EP -->|Processed Events| SG
        SG -->|Trading Signals| TA
        TA -->|Updates| Discord
    end

    subgraph "Sentiment Analysis"
        NF[News Fetcher]
        FA[FinBERT Analyzer]
        NF -->|Articles| FA
        FA -->|Sentiment| NM
    end

    subgraph "Event Types"
        PE[Price Events]
        NE[News Events]
        SE[Signal Events]
    end

    %% Connections
    Alpaca -->|Market Data| PO
    Alpaca -->|Market Status| MH
    EQ -->|Events| PE
    EQ -->|Events| NE
    EQ -->|Events| SE

    %% Styling
    classDef marketHours fill:#f9f,stroke:#333,stroke-width:2px
    classDef components fill:#bbf,stroke:#333,stroke-width:2px
    classDef external fill:#bfb,stroke:#333,stroke-width:2px
    classDef data fill:#fbb,stroke:#333,stroke-width:2px

    class MH,PO,SG,TA marketHours
    class NM,EQ,EP,NF,FA components
    class Alpaca,Discord external
    class PE,NE,SE data
```

## Component Descriptions

### Market Hours Management
- **Market Hours Check**: Continuously monitors market status
- **Price Monitor**: Tracks real-time price data during market hours
- **Sleep**: Manages system state during market closed hours

### 24/7 Components
- **News Monitor**: Continuously monitors news and sentiment
- **Event Queue**: Central message bus for all system events
- **Event Processor**: Processes and routes events

### Market Hours Components
- **Signal Generator**: Generates trading signals based on data
- **Trading Agent**: Makes trading decisions and manages positions

### External Services
- **Alpaca API**: Provides market data and trading capabilities
- **Discord Webhook**: Sends real-time updates and alerts

### Sentiment Analysis
- **News Fetcher**: Retrieves news articles
- **FinBERT Analyzer**: Analyzes sentiment of news

### Event Types
- **Price Events**: Real-time price updates
- **News Events**: News and sentiment updates
- **Signal Events**: Trading signals and decisions 