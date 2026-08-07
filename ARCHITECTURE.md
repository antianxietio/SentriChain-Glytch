# SentriChain System Architecture

This diagram illustrates the high-level system architecture of the SentriChain application, showing the technology stack and how the different layers (Frontend, Backend, Database, and External Services) interact.

```mermaid
architecture-beta
    group client(cloud)[Client]
    group frontend(server)[Frontend: Next.js 16 + React] in client

    group backend(cloud)[Backend: FastAPI]
    group data(database)[Data Layer] in backend
    group external(internet)[External Services]

    service browser(internet)[Web Browser] in client
    service ui(server)[UI Components + Tailwind] in frontend
    service proxy(server)[Next.js API Routes / Server Actions] in frontend

    service router(server)[FastAPI Routers] in backend
    service auth(server)[Auth Service (JWT)] in backend
    service agents(server)[Multi-Agent Risk Engine] in backend
    service orm(server)[SQLAlchemy ORM] in backend

    service db(database)[Relational Database] in data

    service wb(cloud)[World Bank API] in external
    service gdelt(cloud)[GDELT API] in external
    service gemini(cloud)[Gemini API] in external

    browser:R --> L:ui
    ui:R --> L:proxy
    proxy:B --> T:router

    router:L --> R:auth
    router:R --> L:agents
    router:B --> T:orm
    orm:B --> T:db

    agents:R --> L:wb
    agents:R --> L:gdelt
    agents:R --> L:gemini
```
