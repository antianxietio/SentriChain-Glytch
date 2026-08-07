# SentriChain Data Flow Diagram

This diagram maps out how data travels from internal and external sources through the multi-agent engine to eventually reach the user's dashboard. You can view this natively in VS Code if you have a Markdown Preview Mermaid extension installed, or paste it into [Mermaid Live Editor](https://mermaid.live).

```mermaid
flowchart TD
    %% Styling
    classDef internal fill:#e0f2fe,stroke:#4f46e5,stroke-width:2px,color:#0f172a
    classDef external fill:#ecfdf5,stroke:#059669,stroke-width:2px,color:#0f172a
    classDef agent fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#0f172a
    classDef core fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#0f172a
    classDef ui fill:#fff1f2,stroke:#db2777,stroke-width:2px,color:#0f172a

    %% Data Sources
    subgraph Internal_Data [Internal Operational Data]
        UserPref[User Onboarding Profile<br/>Mags, Countries, Industry]:::internal
        DB_Supp[Supplier Master Data<br/>Reliability & Wait Times]:::internal
        DB_Sched[Equipment Schedules<br/>Planned vs Actual Dates]:::internal
    end

    subgraph External_Data [External Intelligence]
        API_WGI[World Bank Data<br/>Stability & Economy]:::external
        API_GDELT[GDELT Project<br/>Live News Events]:::external
        API_LPI[Logistics Data<br/>Shipping & Tariffs]:::external
    end

    %% Agents
    subgraph Risk_Agents [Multi-Agent Risk Engine]
        Agent1(Schedule Variance Agent<br/>Analyzes delays & EVM):::agent
        Agent2(Geopolitical Signal Agent<br/>Analyzes country risk):::agent
        Agent3(Supplier Reliability Agent<br/>Analyzes historical delivery):::agent
    end

    %% Core Logic
    subgraph Core_Engine [Aggregation & AI]
        Ensemble{Ensemble Aggregator<br/>Calculates Risk & Confidence}:::core
        LLM((Gemini LLM<br/>Generates Text Summary)):::core
        RecEngine{Recommendation Engine<br/>Ranks Alternative Suppliers}:::core
    end

    %% Output
    subgraph User_Dashboard [Frontend Dashboard]
        UI_Dash[Supplier Overview]:::ui
        UI_Score[Risk Analysis View]:::ui
        UI_Alts[Personalized Alternatives]:::ui
    end

    %% Flow Connections
    DB_Sched --> Agent1
    API_WGI --> Agent2
    API_GDELT --> Agent2
    DB_Supp --> Agent3

    Agent1 --> Ensemble
    Agent2 --> Ensemble
    Agent3 --> Ensemble

    Ensemble --> LLM
    Ensemble --> UI_Score
    LLM --> UI_Score

    UserPref --> RecEngine
    Ensemble -.-> RecEngine
    DB_Supp --> RecEngine
    API_LPI --> DB_Supp

    RecEngine --> UI_Alts
    DB_Supp --> UI_Dash
    API_WGI --> UI_Dash
```

## How to Explain This (No-Math Presentation Script)

1. **Left Side (The Inputs)**
   "Our system pulls from two main buckets. The top bucket is the company's own data—what they buy, who they buy from, and when deliveries are scheduled. The bottom bucket is live global data—World Bank economic stability, logistics indices, and breaking news events from GDELT."

2. **Middle (The Agents)**
   "All this data feeds into our three independent agents. One agent watches the clock for schedule slips, another watches the globe for political instability, and the third reviews the supplier's historical track record."

3. **Right Side (The Output)**
   "The agents cast their votes to an 'Ensemble Aggregator' that reaches a final consensus. That consensus risk score, along with customized supplier recommendations matching the user's initial onboarding profile, gets pushed straight to the procurement manager's dashboard."
