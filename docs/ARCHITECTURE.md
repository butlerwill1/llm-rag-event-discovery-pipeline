# System Architecture

Technical architecture documentation for the Event Discovery RAG Pipeline.

## AI Model Strategy

The system uses a multi-model approach optimized for different tasks:

| Component | Model | Purpose |
|-----------|-------|---------|
| **Event Discovery** | GPT-5 with web search | Agentic search with reasoning capabilities for multi-step event discovery |
| **Deduplication** | GPT-4o | Fast, cost-effective LLM for semantic duplicate detection |
| **Embeddings** | all-MiniLM-L6-v2 | Local embedding generation (384 dimensions, no API costs) |

This architecture balances cost, performance, and quality by using reasoning models only where needed and eliminating embedding API costs through local generation.

---

## Complete Process Flow

```mermaid
graph TD
    Start([ECS Task Starts]) --> Init[Initialize Components]

    Init --> Weaviate[Connect to Weaviate]
    Init --> LoadModel[Load Local Embedding Model]
    Init --> QueryLoad[Load data/queries.txt]

    Weaviate --> HealthCheck{Weaviate Healthy?}
    HealthCheck -->|No| Wait[Wait & Retry]
    Wait --> HealthCheck
    HealthCheck -->|Yes| Cleanup[Cleanup Past Events]

    Cleanup --> DeleteOld[Delete events where eventDate < today]
    DeleteOld --> Search[Search for Events]

    Search --> Loop{For each query}

    Loop --> GPT5[GPT-5 Agentic Web Search]
    GPT5 --> WebSearch[Multi-step search across platforms]
    WebSearch --> Response[Structured JSON response]

    Response --> Parser[Parse & Validate Events]
    Parser --> Events[List of event objects]

    Events --> Dedupe{For each event}

    Dedupe --> URLCheck{Exact URL match?}
    URLCheck -->|Yes| Skip1[Skip - Duplicate]
    URLCheck -->|No| VectorSearch[Generate Local Embedding]

    VectorSearch --> Retrieve[Vector similarity search]
    Retrieve --> Candidates[Top 5 similar events]
    Candidates --> LLM[GPT-4o Duplicate Analysis]
    LLM --> Decision{Is Duplicate?}

    Decision -->|Yes| Skip2[Skip - Duplicate]
    Decision -->|No| AddEvent[Generate Embedding]

    AddEvent --> Store[Store in Weaviate with Vector]
    Store --> Track[Add to new events list]

    Skip1 --> Next1{More events?}
    Skip2 --> Next1
    Track --> Next1

    Next1 -->|Yes| Dedupe
    Next1 -->|No| Email[Format Email Digest]

    Email --> SES[Send via AWS SES]
    SES --> Exit[Container Exits]
    Exit --> TaskStop[ECS Task Terminates]
    TaskStop --> WALFlush[Weaviate Flushes WAL to EFS]
    WALFlush --> Done([Complete])

    style Init fill:#4A90E2,color:#fff
    style Weaviate fill:#E27D60,color:#fff
    style GPT5 fill:#85CDCA,color:#000
    style LLM fill:#C38D9E,color:#fff
    style SES fill:#41B3A3,color:#fff
```

---

## AWS Infrastructure Architecture

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Scheduling"
            EB[EventBridge Scheduler<br/>Cron: Sunday 9 AM UTC]
        end

        subgraph "Compute - ECS Fargate"
            Task[ECS Task]
            subgraph "Containers"
                App[Event Finder Container<br/>essential=true]
                DB[Weaviate Container<br/>essential=false]
            end
        end

        subgraph "Storage"
            ECR[ECR Repository<br/>Docker Images]
            EFS[EFS Volume<br/>Weaviate Data + WAL]
        end

        subgraph "Networking"
            VPC[VPC]
            SG[Security Group]
            Subnet[Public Subnets]
        end

        subgraph "Monitoring"
            CW[CloudWatch Logs<br/>7-day retention]
        end

        subgraph "Email"
            SES[AWS SES<br/>Email Delivery]
        end
    end

    subgraph "External"
        OpenAI[OpenAI API<br/>GPT-5 + GPT-4o]
    end

    EB -->|Triggers| Task
    Task --> App
    Task --> DB
    App -->|localhost:8080| DB
    DB -->|Mounts| EFS
    Task -->|Pulls from| ECR
    Task -->|Logs to| CW
    App -->|API Calls| OpenAI
    App -->|Sends Email| SES
    Task -->|Runs in| Subnet
    Subnet -->|Part of| VPC
    Task -->|Protected by| SG

    style EB fill:#FF9900,color:#000
    style Task fill:#4A90E2,color:#fff
    style App fill:#85CDCA,color:#000
    style DB fill:#E27D60,color:#fff
    style EFS fill:#E8A87C,color:#000
    style SES fill:#41B3A3,color:#fff
```

---

## RAG Deduplication Flow

```mermaid
sequenceDiagram
    participant M as main.py
    participant W as src/ai_agent/weaviate_client.py
    participant V as Weaviate DB
    participant L as Local Embedding Model
    participant O as OpenAI GPT-4o

    M->>W: is_duplicate(event)

    Note over W: Step 1: Fast Path
    W->>V: Query by exact URL
    V-->>W: Match found?

    alt URL exists
        W-->>M: True (Duplicate)
    else URL not found
        Note over W: Step 2: Semantic Search
        W->>L: Generate embedding for event
        Note over L: all-MiniLM-L6-v2<br/>384 dimensions
        L-->>W: Query vector

        W->>V: Vector similarity search<br/>threshold=0.85, limit=5
        V-->>W: Top 5 similar events

        alt No similar events
            W-->>M: False (Not duplicate)
        else Similar events found
            Note over W: Step 3: LLM Analysis
            W->>O: Analyze: new event vs candidates
            Note over O: Compare:<br/>- Name & Date<br/>- Venue<br/>- Description
            O-->>W: {"is_duplicate": bool, "reason": str}

            alt LLM confirms duplicate
                W-->>M: True (Duplicate)
            else LLM confirms unique
                W-->>M: False (Not duplicate)
                M->>W: add_event(event)
                W->>L: Generate embedding
                L-->>W: Event vector
                W->>V: Store event + vector
            end
        end
    end
```

---

## Container Lifecycle

```mermaid
sequenceDiagram
    participant EB as EventBridge
    participant ECS as ECS Fargate
    participant W as Weaviate Container
    participant A as Event Finder Container
    participant EFS as EFS Volume

    EB->>ECS: Trigger scheduled task
    ECS->>W: Start container (essential=false)
    ECS->>A: Start container (essential=true)

    Note over W: Weaviate starts<br/>Loads WAL from EFS
    W->>EFS: Read persisted data

    Note over A: Wait for Weaviate health check
    A->>W: GET /v1/meta (health)
    W-->>A: Ready

    Note over A: Execute main.py<br/>Search, deduplicate, email
    A->>W: Store events
    W->>EFS: Write to WAL immediately

    Note over A: Execution complete
    A->>A: Exit (code 0)

    Note over ECS: Essential container exited<br/>Terminate task
    ECS->>W: Send SIGTERM

    Note over W: Graceful shutdown<br/>30-second timeout
    W->>EFS: Flush WAL
    EFS-->>W: Acknowledged

    ECS->>W: Send SIGKILL (if needed)

    Note over ECS: Task stopped<br/>Data persisted on EFS
```

---

## Data Persistence Strategy

Weaviate uses a Write-Ahead-Log (WAL) approach for crash recovery:

```mermaid
graph LR
    A[Event Added] --> B[Write to WAL on EFS]
    B --> C[Acknowledge to Client]
    C --> D[Update In-Memory Index]
    D --> E[Periodic Segment Flush]
    E --> F[Mark WAL Complete]

    G[Container Restart] --> H[Check WAL Status]
    H -->|Incomplete| I[Replay WAL]
    H -->|Complete| J[Load Segments]
    I --> J
    J --> K[Ready for Queries]

    style B fill:#E27D60,color:#fff
    style E fill:#E8A87C,color:#000
    style I fill:#C38D9E,color:#fff
```

Key guarantees:
- Every write is persisted to EFS before acknowledgment
- WAL entries are append-only (fast writes)
- Incomplete WAL is replayed on startup
- 30-second SIGTERM grace period ensures final flush

---

## Component Responsibilities

| Component | Purpose | Key Technologies |
|-----------|---------|------------------|
| **main.py** | Orchestration and execution flow | Python, logging |
| **src/ai_agent/openai_client.py** | GPT-5 agentic web search | OpenAI Responses API, web_search tool |
| **src/ai_agent/weaviate_client.py** | Vector database operations | Weaviate v4 API, sentence-transformers |
| **src/ai_agent/event_parser.py** | JSON parsing and validation | Python, data validation |
| **src/ai_agent/email_service.py** | Email digest generation | boto3, AWS SES |
| **src/ai_agent/config.py** | Configuration management | python-dotenv, environment variables |
| **src/ai_agent/query_loader.py** | Query file management | File I/O, text processing |

---

## Technology Stack Summary

**Application Layer**:
- Python 3.11 (runtime)
- OpenAI SDK (GPT-5, GPT-4o)
- Weaviate Client v4 (vector database)
- Sentence Transformers (local embeddings)
- boto3 (AWS SDK)

**Infrastructure**:
- AWS ECS Fargate (serverless containers)
- AWS EventBridge (scheduling)
- AWS ECR (container registry)
- AWS EFS (persistent storage)
- AWS SES (email delivery)
- Terraform (infrastructure as code)
- GitHub Actions (CI/CD)

**Data & AI**:
- Weaviate 1.27.5 (vector database)
- all-MiniLM-L6-v2 (embedding model, 384 dimensions)
- GPT-5 with web search (event discovery)
- GPT-4o (deduplication)

---

For detailed process flow documentation, see [PROCESS_FLOW.md](./PROCESS_FLOW.md).
