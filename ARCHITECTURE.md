# 🏗️ System Architecture & Process Flow

This document provides a visual overview of how the London Events AI Agent works.

---

## 🔄 Complete Process Flow

```mermaid
graph TD
    Start([User runs: python main.py]) --> Main[main.py]
    
    Main --> Init[Initialize Components]
    Init --> Config[config.py: Load env vars]
    Init --> Weaviate[weaviate_client.py: Connect to Weaviate]
    Init --> QueryLoad[query_loader.py: Load queries.txt]
    
    QueryLoad --> Queries[queries.txt: List of search queries]
    
    Main --> Cleanup[Cleanup Past Events]
    Cleanup --> WeavClean[weaviate_client.cleanup_past_events]
    WeavClean --> DeleteOld[Delete events where eventDate < today]
    
    Main --> Search[Search for Events]
    Search --> Loop{For each query}
    
    Loop --> OpenAI[openai_client.py: Call OpenAI API]
    OpenAI --> WebSearch[OpenAI searches web for events]
    WebSearch --> Response[Raw JSON response]
    
    Response --> Parser[event_parser.py: Parse response]
    Parser --> Extract[Extract structured event data]
    Extract --> Events[List of event dictionaries]
    
    Events --> Dedupe{For each event}
    
    Dedupe --> CheckDup[weaviate_client.is_duplicate]
    CheckDup --> URLCheck{Exact URL match?}
    URLCheck -->|Yes| Skip1[Skip - Duplicate]
    URLCheck -->|No| RAG[RAG-Powered Check]
    
    RAG --> Retrieve[Retrieve top 5 similar events]
    Retrieve --> LLM[Ask GPT-4o: Is this duplicate?]
    LLM --> Decision{LLM Decision}
    
    Decision -->|Duplicate| Skip2[Skip - Duplicate]
    Decision -->|Not Duplicate| Add[weaviate_client.add_event]
    
    Add --> Embed[Generate embedding via OpenAI]
    Embed --> Store[Store in Weaviate vector DB]
    Store --> Track[Add to newly_added_events list]
    
    Skip1 --> Next1{More events?}
    Skip2 --> Next1
    Track --> Next1
    
    Next1 -->|Yes| Dedupe
    Next1 -->|No| Summary[Generate Summary]
    
    Summary --> Count[weaviate_client.get_event_count]
    Summary --> GetAll[weaviate_client.get_all_events]
    Summary --> Display[Display statistics]
    
    Display --> Email[Send Email Digest]
    Email --> EmailSvc[email_service.py]
    EmailSvc --> Format[Format HTML email]
    Format --> SES[Send via AWS SES]
    SES --> Done([Complete])
    
    style Main fill:#4A90E2,color:#fff
    style Weaviate fill:#E27D60,color:#fff
    style OpenAI fill:#85CDCA,color:#000
    style Parser fill:#E8A87C,color:#000
    style LLM fill:#C38D9E,color:#fff
    style EmailSvc fill:#41B3A3,color:#fff
```

---

## 📦 Component Architecture

```mermaid
graph LR
    subgraph "User Interface"
        CLI[Command Line]
        Docker[Docker Compose]
    end
    
    subgraph "Application Layer"
        Main[main.py<br/>Orchestrator]
        Query[query_loader.py<br/>Query Manager]
        Parser[event_parser.py<br/>JSON Parser]
    end
    
    subgraph "AI Services"
        OpenAI[openai_client.py<br/>Web Search]
        Weaviate[weaviate_client.py<br/>Vector DB Client]
    end
    
    subgraph "External Services"
        GPT[OpenAI API<br/>GPT-4o + Embeddings]
        VectorDB[(Weaviate<br/>Vector Database)]
        SES[AWS SES<br/>Email Service]
    end
    
    subgraph "Output"
        Email[email_service.py<br/>Email Formatter]
        Inbox[📧 User Inbox]
    end
    
    CLI --> Main
    Docker --> Main
    Main --> Query
    Main --> OpenAI
    Main --> Parser
    Main --> Weaviate
    Main --> Email
    
    OpenAI --> GPT
    Weaviate --> GPT
    Weaviate --> VectorDB
    Email --> SES
    SES --> Inbox
    
    style Main fill:#4A90E2,color:#fff
    style Weaviate fill:#E27D60,color:#fff
    style OpenAI fill:#85CDCA,color:#000
    style Email fill:#41B3A3,color:#fff
    style GPT fill:#C38D9E,color:#fff
    style VectorDB fill:#E8A87C,color:#000
```

---

## 🔍 RAG Deduplication Flow

```mermaid
sequenceDiagram
    participant M as main.py
    participant W as weaviate_client.py
    participant V as Weaviate DB
    participant O as OpenAI API
    
    M->>W: is_duplicate(event)
    
    Note over W: Step 1: Fast Path
    W->>V: Check exact URL match
    V-->>W: URL exists?
    
    alt URL exists
        W-->>M: True (Duplicate)
    else URL not found
        Note over W: Step 2: RAG Path
        W->>V: Vector search for similar events
        Note over V: Semantic search using embeddings
        V-->>W: Top 5 similar events
        
        W->>O: Ask GPT-4o: Is this duplicate?
        Note over O: LLM analyzes:<br/>- Event name<br/>- Date<br/>- Venue<br/>- Description
        O-->>W: {"is_duplicate": bool, "reason": str}
        
        alt LLM says duplicate
            W-->>M: True (Duplicate)
        else LLM says unique
            W-->>M: False (Not duplicate)
            M->>W: add_event(event)
            W->>O: Generate embedding
            O-->>W: Vector embedding
            W->>V: Store event + embedding
        end
    end
```

---

## 📊 Data Flow

```mermaid
flowchart LR
    A[queries.txt] --> B[OpenAI Web Search]
    B --> C[Raw JSON Response]
    C --> D[event_parser.py]
    D --> E[Structured Events]
    E --> F{RAG Deduplication}
    F -->|Duplicate| G[Skip]
    F -->|Unique| H[Weaviate Vector DB]
    H --> I[email_service.py]
    I --> J[AWS SES]
    J --> K[📧 User Inbox]
    
    style F fill:#C38D9E,color:#fff
    style H fill:#E27D60,color:#fff
    style K fill:#41B3A3,color:#fff
```

---

## 🐳 Docker Architecture

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "Service 1: Weaviate"
            WV[Weaviate Container<br/>Port 8080]
            VOL1[(Volume:<br/>weaviate_data)]
        end
        
        subgraph "Service 2: Event Finder"
            APP[Python App Container<br/>main.py]
            ENV[Environment Variables<br/>.env file]
        end
    end
    
    APP -->|HTTP| WV
    WV --> VOL1
    ENV --> APP
    
    APP -->|API Calls| OPENAI[OpenAI API]
    APP -->|Send Email| SES[AWS SES]
    
    style WV fill:#E27D60,color:#fff
    style APP fill:#4A90E2,color:#fff
    style VOL1 fill:#E8A87C,color:#000
```

---

## 🔑 Key File Responsibilities

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| **main.py** | Orchestrates entire process | queries.txt | Email digest |
| **config.py** | Loads environment variables | .env file | Configuration constants |
| **query_loader.py** | Manages search queries | queries.txt | List of queries |
| **openai_client.py** | Calls OpenAI for web search | Search query | Raw JSON events |
| **event_parser.py** | Parses & validates events | Raw JSON | Structured dicts |
| **weaviate_client.py** | Vector DB operations | Events | Stored/retrieved events |
| **email_service.py** | Sends email digests | Event list | Sent email |
| **rag_query.py** | Interactive CLI queries | User question | AI answer |

---

## 🎯 Technology Stack

```mermaid
mindmap
  root((London Events<br/>AI Agent))
    Python 3.11
      main.py
      Libraries
        openai
        weaviate-client
        boto3
    Vector Database
      Weaviate
        Semantic Search
        Auto Embeddings
    AI Models
      GPT-4o
        Web Search
        Deduplication
      text-embedding-3-small
        Vector Embeddings
    Cloud Services
      AWS SES
        Email Delivery
    Infrastructure
      Docker
        docker-compose
        Containers
      Terraform (planned)
        ECS Fargate
        ECR
```

---

For detailed code examples and step-by-step explanations, see [PROCESS_FLOW.md](./PROCESS_FLOW.md).

