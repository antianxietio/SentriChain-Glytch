
# 🌍 Sentrichain — Intelligent Supply Chain Risk Management Platform

Sentrichain transforms supply chain risk analysis into a fast, data-driven, and visually interactive experience.  
Built for the **VIT Chennai Hackathon 2025**, this project demonstrates a practical AI-powered workflow for predicting risk, estimating financial impact, and recommending smarter sourcing decisions.

---

## 🚀 Key Features (Hackathon MVP)

### ✅ Backend (FastAPI)
- `/api/analyze` — schedule risk, cost impact, alternatives, summary  
- `/api/suppliers` — list suppliers  
- Clean DB schema + seeded sample data  

### 🎨 Frontend (Next.js)
- Interactive dashboard  
- 3D supply chain globe  
- Dynamic cards for risk, cost, alternatives  
- Basic voice-triggered analysis  
- Smooth UI & responsive design  

### 📡 Integrations (Demo)
- WhatsApp alert trigger  
- Fallback JSON mocks  
- Optional LLM summary  

---

## 🏛️ Tech Stack

### Backend  
- FastAPI  
- SQLAlchemy  
- Azure SQL / SQLite  
- Python 3.11+

### Frontend  
- Next.js 14  
- React 18  
- Tailwind CSS  
- react-globe.gl / Three.js  

---

## 📁 Project Structure

\`\`\`
sentrichain/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   ├── seed.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── styles/
│   └── package.json
│
└── README.md
\`\`\`

---

## 🧧 Getting Started

### 1. Clone Repository  
\`\`\`
git clone https://github.com/<your-username>/sentrichain.git
\`\`\`

### 2. Backend Setup  
\`\`\`
cd sentrichain/backend
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
\`\`\`

### 3. Frontend Setup  
\`\`\`
cd sentrichain/frontend
npm install
npm run dev
\`\`\`

---

## 🧪 API Overview

### **POST /api/analyze**
Returns:
- schedule risk  
- cost impact  
- top 3 alternatives  
- executive summary  

### **GET /api/suppliers**
Returns:
- supplier list for dropdowns  

---

## 👥 Team Roles (Hackathon)
- Backend Core  
- Database & Data Prep  
- Frontend UI  
- Globe Visualization  
- Integration + Demo Flow  

---

## 📄 License
MIT License (optional)


