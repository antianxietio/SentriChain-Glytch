# 🌍 SentriChain — Intelligent Supply Chain Risk Management Platform

SentriChain transforms supply chain risk analysis into a fast, data-driven, and visually interactive experience.  
Built for the **VIT Chennai Hackathon 2025**, this project demonstrates a practical AI-powered workflow for predicting risk, estimating financial impact, and recommending smarter sourcing decisions.

---

## 🚀 Key Features

### ✅ Backend (FastAPI)

- **RESTful API** with FastAPI framework
- **SQLAlchemy ORM** for database management
- **Environment-based configuration** with python-dotenv
- **Database session management** with dependency injection
- **CORS middleware** for cross-origin requests
- **Auto-generated API documentation** (Swagger UI)

### 🎯 Core Endpoints (Ready for Business Logic)

- `POST /api/analyze` — Risk analysis and cost impact calculations
- `GET /api/suppliers` — Supplier listing and management
- `GET /` — Health check and API status
- `GET /health` — System health monitoring

### 📡 Future Integrations

- WhatsApp alert triggers
- LLM-powered summaries
- Real-time data feeds
- 3D supply chain visualization

---

## 🏛️ Tech Stack

### Backend

- **FastAPI** — Modern, fast web framework
- **SQLAlchemy** — SQL toolkit and ORM
- **Uvicorn** — ASGI server
- **Python-dotenv** — Environment variable management
- **Python 3.11+**

### Database

- **SQLite** (development)
- **PostgreSQL/Azure SQL** (production-ready)

---

## 📁 Project Structure

```
SentriChain-Glytch/
│
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # SQLAlchemy engine, session, and Base
│   ├── routers/
│   │   └── __init__.py      # API route handlers
│   ├── models/
│   │   └── __init__.py      # SQLAlchemy models (ready for implementation)
│   ├── schemas/
│   │   └── __init__.py      # Pydantic schemas (ready for implementation)
│   ├── utils/
│   │   └── __init__.py      # Utility functions
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (DATABASE_URL)
│
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### 1. Clone Repository

```bash
git clone https://github.com/antianxietio/SentriChain-Glytch.git
cd SentriChain-Glytch
```

### 2. Backend Setup

#### Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

#### Configure Environment

The `.env` file is already configured with SQLite:

```env
DATABASE_URL=sqlite:///./sentrichain.db
```

For PostgreSQL or Azure SQL, update to:

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
```

#### Run the Server

```powershell
uvicorn main:app --reload
```

The server will start at **http://localhost:8000**

---

## 🧪 Testing the Backend

### Method 1: Interactive API Documentation (Recommended)

FastAPI auto-generates interactive API documentation:

1. **Start the server:**

   ```powershell
   cd backend
   uvicorn main:app --reload
   ```

2. **Open Swagger UI in your browser:**

   ```
   http://localhost:8000/docs
   ```

3. **Test endpoints interactively:**

   - Click on any endpoint (POST /api/analyze, GET /api/suppliers)
   - Click "Try it out"
   - Fill in parameters (if needed)
   - Click "Execute"
   - View the response

4. **Alternative documentation (ReDoc):**
   ```
   http://localhost:8000/redoc
   ```

### Method 2: PowerShell (curl/Invoke-WebRequest)

#### Test Health Endpoint

```powershell
# Simple health check
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content

# Or using curl (if installed)
curl http://localhost:8000/health
```

#### Test GET /api/suppliers

```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/suppliers | Select-Object -ExpandProperty Content
```

#### Test POST /api/analyze

```powershell
$body = @{} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/analyze -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content
```

### Method 3: Using Python Requests

Create a test file `test_api.py`:

```python
import requests

BASE_URL = "http://localhost:8000"

# Test health check
response = requests.get(f"{BASE_URL}/health")
print("Health Check:", response.json())

# Test suppliers endpoint
response = requests.get(f"{BASE_URL}/api/suppliers")
print("Suppliers:", response.json())

# Test analyze endpoint
response = requests.post(f"{BASE_URL}/api/analyze")
print("Analyze:", response.json())
```

Run it:

```powershell
python test_api.py
```

### Method 4: Using Browser

Simple GET requests can be tested directly in browser:

- Health: http://localhost:8000/health
- Root: http://localhost:8000/
- Suppliers: http://localhost:8000/api/suppliers

### Expected Responses

#### GET /health

```json
{
  "status": "healthy"
}
```

#### GET /

```json
{
  "message": "SentriChain API is running",
  "version": "0.1.0",
  "status": "healthy"
}
```

#### GET /api/suppliers

```json
{
  "message": "suppliers placeholder",
  "suppliers": [],
  "status": "not_implemented"
}
```

#### POST /api/analyze

```json
{
  "message": "analyze placeholder",
  "status": "not_implemented"
}
```

### Verify Database Connection

The server will automatically create `sentrichain.db` in the backend folder when it starts. Check for:

- File exists: `backend/sentrichain.db`
- No database connection errors in console
- Endpoints respond without 500 errors

---

## 🔧 Development Workflow

### Adding New Models

1. Create model classes in `models/__init__.py`
2. Import from `database import Base`
3. Restart server to create tables

### Adding New Endpoints

1. Add route handlers in `routers/__init__.py`
2. Use `Depends(get_db)` for database access
3. Auto-reload will pick up changes

### Adding Pydantic Schemas

1. Define request/response models in `schemas/__init__.py`
2. Use for validation and documentation

---

## 📊 Next Steps

- [ ] Implement SQLAlchemy models for suppliers, risks, analyses
- [ ] Create Pydantic schemas for request/response validation
- [ ] Add business logic to endpoint handlers
- [ ] Implement data seeding script
- [ ] Add authentication and authorization
- [ ] Connect to external APIs (risk data, pricing)
- [ ] Build frontend dashboard
- [ ] Deploy to production

---

## 🛠️ Troubleshooting

### Server won't start

- Check Python version: `python --version` (needs 3.11+)
- Verify dependencies: `pip install -r requirements.txt`
- Check port 8000 isn't in use

### Database errors

- Verify `.env` file exists in backend folder
- Check DATABASE_URL format
- Ensure write permissions for SQLite file

### Import errors

- Run from `backend/` directory
- Check all `__init__.py` files exist
- Verify virtual environment is activated (if using one)

---

## 👥 Contributing

This is a hackathon project. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push and create a Pull Request

---

## 📄 License

MIT License — Free to use and modify

---

## 🏆 Built for VIT Chennai Hackathon 2025

**Project:** SentriChain  
**Focus:** AI-powered supply chain risk management  
**Status:** Backend skeleton complete ✅
