# 🌀 Miasma Filter  
**AI-Powered Real-Time Misinformation Detection for Live Streams**  
_A project by Team ADROIT (GenAI Exchange Hackathon, Breakthrough Concept Award)_  

---

## 🌍 Problem Statement
False news spreads **6× faster than truth** (MIT study). In **live streams**, misinformation snowballs instantly — leaving no buffer for fact-checking.  
Traditional moderation tools **only flag static content after upload**, but by then, millions may already be misled.  

👉 **Miasma Filter** solves this by inserting an **AI-powered verification layer** between content creators and viewers, ensuring only **verified claims** pass through live streams.  

---

## 🚀 Features
- 🔴 **Real-Time Multimodal Verification** – Speech, text, video signals verified instantly  
- ⚡ **Low-Latency Streaming** – AI-powered verification without delays  
- 🧠 **Agentic AI Pipeline** – Supervisor → Fact Checker → Reporter → User  
- 🗄️ **Dynamic Fact Store** – Redis-backed cache, refreshed continuously  
- 📊 **Confidence Scoring** – Transparent explainable outputs with evidence  
- 🔔 **Live Alerts & Overlays** – Blocks misinformation before reaching viewers  
- 🏆 **Creator Credibility Scoring** – Builds trust scores for broadcasters  

---

## 🛠 Tech Stack
| Category      | Technology / Service | Purpose |
|---------------|----------------------|---------|
| **Frontend**  | Next.js + TailwindCSS | Viewer & broadcaster interface |
| **Backend**   | FastAPI (Python)     | Core logic & APIs |
| **Database**  | Redis                | Real-time cache & fact store |
| **GenAI**     | Gemini 2.5 Pro, Gemini Flash Live | Claim detection & reasoning |
| **Streaming** | Gemini Live API + WebSockets | Bidi-streaming for AI processing |
| **Agents**    | Google Agent Dev Kit (ADK) | Multi-agent pipeline |
| **Search**    | Vertex AI Search     | Fact verification sources |

---

## 📂 Project Structure
```
miasma-filter/
├── frontend/          # Next.js frontend
│   ├── pages/         # Next.js pages
│   ├── components/    # UI components
│   ├── styles/        # Tailwind styles
│   └── utils/         # Helpers
│
├── backend/           # FastAPI backend
│   ├── main.py        # Entrypoint
│   ├── websocket.py   # Live communication
│   ├── agents/        # Supervisor, Fact Checker, Reporter
│   ├── cache/         # Redis logic
│   ├── utils/         # Helpers
│   └── requirements.txt
│
├── docker-compose.yml # For running full stack
└── README.md          # This file
```

---

## ⚙️ Setup Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-repo/miasma-filter.git
cd miasma-filter
```

---

### 2️⃣ Frontend (Next.js)
```bash
cd frontend
npm install
```

Create `.env.local`:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

Run development server:
```bash
npm run dev
```
👉 Open [http://localhost:3000](http://localhost:3000)

---

### 3️⃣ Backend (FastAPI)
```bash
cd backend
python -m venv .env
source .env/bin/activate   # Linux/Mac
.env\Scripts\activate      # Windows
pip install -r requirements.txt
```

Run Redis (Docker example):
```bash
docker run -d -p 6379:6379 redis
```

Create `.env`:
```env
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_api_key
VERTEX_API_KEY=your_vertex_ai_key
```

Start FastAPI:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 4️⃣ Run Full Stack with Docker (Optional)
If you have `docker-compose.yml`, just run:
```bash
docker-compose up --build
```

This will start:
- Frontend on `http://localhost:3000`
- Backend on `http://localhost:8000`

---

## 📦 Deployment
- **Frontend**: Deploy on **Vercel / Netlify** (set backend URL in env vars)  
- **Backend**: Deploy on **GCP Cloud Run / AWS EC2 / Azure App Service**  
- **Redis**: Use **Managed Redis (GCP Memorystore / AWS ElastiCache)**  
- **SSL (HTTPS + WSS)** required for WebSocket communication  

---

## 🔮 Example Workflow
1. A live stream starts → audio/video/text fed into **Miasma Filter**  
2. **Supervisor Agent** extracts claims in real time  
3. **Fact Checker Agent** verifies claims using trusted sources  
4. **Reporter Agent** generates:  
   - ✅ True/False verdict  
   - 📊 Confidence score  
   - 📑 Evidence sources  
5. Frontend overlays decision in live stream instantly  

---



---

## 📜 License
MIT License © 2025 Team ADROIT
