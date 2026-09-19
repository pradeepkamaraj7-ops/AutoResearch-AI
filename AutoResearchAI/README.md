# AutoResearch AI 🏎️⚡
### AI-Powered Automotive Web Research and Intelligent Answering System

AutoResearch AI is a production-ready automotive research platform that synthesizes natural-language vehicle queries with real-time web discovery, **Crawl4AI** webpage extraction, and **Groq AI** reasoning. It extracts verified technical specifications, generates side-by-side vehicle comparisons with conflict detection, and tracks full source provenance.

---

## Architecture & Data Flow

```
User Query (Text or Voice)
        ↓
FastAPI Backend (/api/research)
        ↓
Query Understanding & Entity Extraction
(Identifies Query Type + Target Vehicles)
        ↓
Authoritative URL Discovery
(OEM Portals, ARAI, NHTSA, CarDekho, ZigWheels)
        ↓
URL Validation & SSRF Guard
(Enforces safe HTTP/HTTPS, blocks private IPs & loopbacks)
        ↓
Crawl4AI Web Extraction
(Async browser extraction + HTTP fallback, cleans Markdown & removes noise)
        ↓
Groq AI Synthesis (groq/compound or llama-3.3-70b-versatile)
(Cross-references specs, detects conflicts, formats structured cards)
        ↓
SQLite Database (aiosqlite)
(Saves query, structured specifications, comparison matrix & sources)
        ↓
Modern Automotive UI (HTML5 / CSS3 / Vanilla JS)
(Renders Summary, Key Specs, Comparison Table, Findings, and Verified Sources)
```

---

---

## Key Features

- **Universal Vehicle Research**: Research ANY car model worldwide—from Indian icons (Tata Nexon, Mahindra Thar Roxx, Scorpio-N, Creta) to global exotics (Porsche 911 GT3, Ferrari 296 GTB, Tesla Cybertruck, BMW M3).
- **Automobile Engineering & Data Answers**: Answers ANY automobile question (powertrain dynamics, dual-clutch vs torque converter, turbochargers, LFP vs NMC battery chemistry, OBD2 diagnostic fault codes).
- **🧠 Deep Thinker Mode**: Rigorous engineering breakdown evaluating mechanical architecture, thermal efficiencies, aerodynamic drag equations, and total cost of ownership (TCO).
- **📄 Instant Vehicle Dossier Reports**: Complete printable technical report (`POST /api/report`) featuring engineering specs, pros & cons, chassis rigidity, safety, and final verdict.
- **🎙️ Interactive Voice Assistant (Speech Recognition + TTS)**: Hands-free voice search with real-time soundwave visualization and text-to-speech audio narration of summaries.
- **Car Comparison with Conflict Flags**: Compares up to 4 vehicles across 11 key attributes and flags conflicting figures (`"Conflicting information found"`).
- **Crawl4AI Integration**: Asynchronous, rate-limited crawling that extracts clean markdown while respecting site terms, robots.txt, and timeouts.
- **Modular Database**: Built on asynchronous SQLite with a clean repository pattern ready for PostgreSQL.
- **Zero Frontend Secrets**: API keys are strictly confined to the backend `.env`.

---

## Directory Structure

```
AutoResearchAI/
│
├── backend/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI server, endpoints, and static file serving
│   ├── config.py            # Environment configuration & path resolution
│   ├── crawler.py           # Crawl4AI async scraper & HTTP fallback
│   ├── groq_service.py      # Groq AI client, entity extraction & synthesis
│   ├── schemas.py           # Pydantic models for validation & responses
│   ├── database.py          # Asynchronous SQLite storage & repository
│   └── requirements.txt     # Python backend dependencies
│
├── frontend/
│   ├── index.html           # Modern automotive dashboard UI
│   ├── style.css            # Automotive design system (Dark navy, blue accents)
│   ├── app.js               # State manager, voice search & API connector
│   └── assets/
│       └── images/
│           └── logo.svg     # AutoResearch AI brand badge
│
├── data/
│   └── autoresearch.db      # SQLite database (auto-created)
│
├── .env.example             # Template environment variables
├── .gitignore               # Standard exclusions for secrets & caches
└── README.md                # Comprehensive documentation
```

---

## Getting Started (Windows PowerShell)

### Prerequisites
- **Python 3.10+** (Python 3.11 recommended)
- Modern web browser (Chrome, Edge, Firefox, Brave)

---

### Step 1: Clone or Navigate to Project Directory
```powershell
cd c:\Users\prade\Desktop\pradeep3\AutoResearchAI
```

### Step 2: Create a Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell execution policy prevents running scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 4: Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 5: Configure Environment Variables
Create `.env` from the example template:
```powershell
Copy-Item .env.example .env
```
Edit `.env` in your text editor (e.g. VS Code, Notepad):
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=groq/compound
HOST=0.0.0.0
PORT=8000
```
> **Note**: AutoResearch AI runs locally with verified automotive knowledge even before adding a key. Adding your `GROQ_API_KEY` activates real-time Groq generative reasoning and compound search.

### Step 6: Setup Crawl4AI (If not already initialized)
```powershell
crawl4ai-setup
playwright install chromium
```

### Step 7: Launch the FastAPI Application
From inside `AutoResearchAI/`:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 8: Open the Frontend
Open your browser to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

The FastAPI server directly hosts the frontend interface and provides interactive Swagger API documentation at:
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Testing & Verifying Endpoints

### 1. Health Check
```powershell
curl http://127.0.0.1:8000/api/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "groq_configured": true,
  "crawl4ai_available": true,
  "db_connected": true,
  "version": "1.0.0",
  "timestamp": "2026-09-18T..."
}
```

### 2. Research Endpoint (Vehicle Comparison)
```powershell
curl -X POST http://127.0.0.1:8000/api/research `
  -H "Content-Type: application/json" `
  -d '{"query": "Compare Tata Nexon EV and Hyundai Creta Electric"}'
```

### 3. Dedicated Comparison Endpoint
```powershell
curl -X POST http://127.0.0.1:8000/api/compare `
  -H "Content-Type: application/json" `
  -d '{"vehicles": ["Tata Nexon EV", "Hyundai Creta Electric"]}'
```

### 4. Vehicle Specifications Lookup
```powershell
curl http://127.0.0.1:8000/api/vehicle/Mahindra%20XUV700
```

### 5. Research History
```powershell
curl http://127.0.0.1:8000/api/history
```

### 6. Authoritative Sources Directory
```powershell
curl http://127.0.0.1:8000/api/sources
```

---

## Example Queries to Try

| Category | Example Query |
| :--- | :--- |
| **Comparison** | `Compare Tata Nexon EV and Hyundai Creta Electric` |
| **Specifications** | `Give specifications of Mahindra XUV700` |
| **EV Market Guide** | `Best EVs under ₹20 lakh in India` |
| **Fuel Economy** | `Compare mileage of popular petrol SUVs` |
| **Safety & Crash Test**| `What is the Bharat NCAP safety rating of Tata Curvv EV?` |
| **Battery & Charging** | `What is the battery capacity and charging time of MG Windsor EV?` |

---

## Authoritative Automotive Source Hierarchy

1. **Official OEM Manufacturer Portals**: Official specifications, battery warranties, motor outputs, standard equipment.
2. **Statutory Certifying Bodies**:
   - **ARAI (Automotive Research Association of India)**: Certified Indian Driving Cycle (MIDC) fuel economy and EV range.
   - **Bharat NCAP & Global NCAP / NHTSA**: Crash safety ratings, adult/child occupant protection scores.
3. **Automotive Research Portals (CarDekho, ZigWheels, CarWale, Autocar India)**: Real-world road tests, ex-showroom and on-road pricing, user owner reviews.

---

## Security & Reliability Architecture

- **Zero Secrets in Frontend**: `GROQ_API_KEY` is loaded strictly by `backend/config.py` and is never exposed in client requests or responses.
- **SSRF Prevention**: `crawler.py` parses and validates every target URL, strictly rejecting `localhost`, `127.0.0.1`, RFC1918 private IP subnets, and non-HTTP schemes.
- **Anti-Bot & Rate Limits**: Bounded concurrency (`MAX_CRAWL_PAGES = 3`) and timeouts prevent aggressive request spikes.
- **Graceful Error Handling**: If Groq or web crawling fails, friendly messages are returned (`"AI service temporarily unavailable."` or `"Unable to retrieve this webpage."`) without exposing raw Python tracebacks.
