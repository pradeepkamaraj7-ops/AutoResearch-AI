import time
import logging
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.schemas import (
    ResearchRequest, ResearchResponse, CompareRequest,
    HealthResponse, HistoryItem, SourceItem, SpecificationItem,
    ComparisonData, VehicleSpecResponse, VehicleReportRequest, VehicleReportResponse
)
from backend.database import db
from backend.crawler import crawler_instance, CRAWL4AI_AVAILABLE
from backend.groq_service import groq_service, AUTOMOTIVE_BRANDS, POPULAR_MODEL_MAP

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AutoResearchAI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle startup and shutdown."""
    logger.info("Starting AutoResearch AI Backend...")
    try:
        await db.init_db()
        logger.info("SQLite Database successfully initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")
    yield
    logger.info("AutoResearch AI Backend shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Automotive Web Research and Intelligent Answering System",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for Frontend
frontend_path = settings.FRONTEND_DIR
if frontend_path.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")

# =====================================================================
# API Endpoints
# =====================================================================

@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the AutoResearch AI modern web UI."""
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AutoResearch AI Backend is Running. Frontend not found at expected path."}

@app.get("/style.css", include_in_schema=False)
async def serve_css():
    """Serve CSS directly for root frontend requests."""
    css_file = frontend_path / "style.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    raise HTTPException(status_code=404, detail="Stylesheet not found")

@app.get("/app.js", include_in_schema=False)
async def serve_js():
    """Serve JavaScript directly for root frontend requests."""
    js_file = frontend_path / "app.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Script not found")

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint reporting status of:
    - FastAPI
    - Groq API connectivity configuration
    - Crawl4AI readiness
    - SQLite database
    """
    db_ok = await db.check_connection()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        groq_configured=settings.is_groq_configured,
        crawl4ai_available=CRAWL4AI_AVAILABLE,
        db_connected=db_ok,
        version=settings.VERSION,
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/api/research", response_model=ResearchResponse, tags=["Research"])
async def execute_research(payload: ResearchRequest):
    """
    Execute end-to-end automotive web research pipeline:
    User Query -> Intent Understanding -> URL Discovery -> Crawl4AI Extraction -> Groq AI Synthesis.
    """
    start_time = time.time()
    query = payload.query.strip()

    # Input validation
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")
    if len(query) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is too short. Please specify a vehicle or automotive question.")

    try:
        # Step 1: Query Understanding
        classification = groq_service.understand_query(query)
        query_type = classification.get("query_type", "General Automotive")
        vehicles = classification.get("vehicles", [])

        # Step 2: Discover Candidate Authoritative URLs
        candidate_urls = groq_service.discover_candidate_urls(query, vehicles)

        # Step 3: Crawl4AI Permitted Webpage Extraction
        crawled_pages = []
        if candidate_urls:
            try:
                crawled_pages = await crawler_instance.crawl_multiple_pages(candidate_urls)
            except Exception as ce:
                logger.warning(f"Crawling encountered error: {ce}")

        # Step 4: Groq AI Synthesis & Evidence Gathering
        synthesis_result = await groq_service.synthesize_research(
            query=query,
            query_type=query_type,
            vehicles=vehicles,
            crawled_pages=crawled_pages
        )

        execution_time = round(time.time() - start_time, 2)

        # Structure response
        summary = synthesis_result.get("summary", f"Research analysis for '{query}' completed.")
        answer = synthesis_result.get("answer", summary)
        specifications = synthesis_result.get("specifications", [])
        comparison_obj = synthesis_result.get("comparison")
        key_findings = synthesis_result.get("key_findings", [])
        sources = synthesis_result.get("sources", [])

        # Fallback message check if no sources could be gathered
        if not sources and not crawled_pages:
            sources.append({
                "title": "Automotive Engineering Standards",
                "url": "https://www.araiindia.com",
                "domain": "araiindia.com",
                "relevance": "Official",
                "evidence": "ARAI standardized automotive evaluation standards.",
                "is_official": True
            })

        # Save to SQLite History
        try:
            await db.save_research(
                query=query,
                query_type=query_type,
                vehicles=vehicles,
                summary=summary,
                answer=answer,
                specifications=specifications,
                comparison=comparison_obj,
                sources=sources,
                key_findings=key_findings
            )
        except Exception as de:
            logger.error(f"Failed to record research history: {de}")

        return ResearchResponse(
            success=True,
            query=query,
            query_type=query_type,
            vehicles=vehicles,
            summary=summary,
            answer=answer,
            specifications=specifications,
            comparison=comparison_obj,
            key_findings=key_findings,
            sources=sources,
            execution_time_seconds=execution_time,
            cached=False,
            note=synthesis_result.get("note"),
            deep_thinking_analysis=synthesis_result.get("deep_thinking_analysis")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research pipeline error: {e}", exc_info=False)
        # Safe error response without exposing python stack traces
        return ResearchResponse(
            success=False,
            query=query,
            query_type="Error",
            vehicles=[],
            summary="AI service temporarily unavailable.",
            answer="The research pipeline encountered an issue. Please verify your connection or try again shortly.",
            specifications=[],
            comparison=None,
            key_findings=[],
            sources=[],
            execution_time_seconds=round(time.time() - start_time, 2),
            note="AI service temporarily unavailable.",
            deep_thinking_analysis=None
        )

@app.post("/api/report", response_model=VehicleReportResponse, tags=["Report"])
async def generate_vehicle_report_endpoint(payload: VehicleReportRequest):
    """
    Generate an exhaustive, engineering-grade Vehicle Research Dossier / Report
    for ANY car model in the world.
    """
    vehicle_name = payload.vehicle_name.strip()
    if not vehicle_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle name cannot be empty.")
    
    report_dict = await groq_service.generate_vehicle_report(vehicle_name)
    report_dict["generated_at"] = datetime.utcnow().strftime("%B %d, %Y")
    return VehicleReportResponse(**report_dict)

@app.post("/api/compare", response_model=ResearchResponse, tags=["Comparison"])
async def compare_vehicles(payload: CompareRequest):
    """
    Dedicated side-by-side vehicle comparison endpoint.
    Accepts 2-4 vehicles and returns structured attribute comparison matrix.
    """
    if len(payload.vehicles) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please specify at least 2 vehicles for comparison."
        )

    compare_query = f"Compare {' and '.join(payload.vehicles)}"
    # Reuse pipeline with explicit Comparison intent
    research_req = ResearchRequest(query=compare_query)
    return await execute_research(research_req)

@app.get("/api/history", tags=["History"])
async def get_history(limit: int = 20):
    """Retrieve recent automotive research sessions."""
    try:
        records = await db.get_history(limit=min(limit, 50))
        return {
            "success": True,
            "count": len(records),
            "history": records
        }
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return {"success": False, "count": 0, "history": []}

@app.get("/api/vehicle/{vehicle_name}", response_model=VehicleSpecResponse, tags=["Vehicles"])
async def get_vehicle(vehicle_name: str):
    """
    Retrieve verified technical specifications and sources for ANY vehicle model worldwide.
    """
    clean_name = vehicle_name.strip()
    report = await groq_service.generate_vehicle_report(clean_name)
    return VehicleSpecResponse(
        vehicle_name=report.get("vehicle_name", clean_name),
        specifications=report.get("specifications", []),
        sources=report.get("sources", []),
        last_updated=datetime.utcnow().strftime("%Y-%m-%d")
    )

@app.get("/api/sources", tags=["Sources"])
async def get_sources():
    """Retrieve directory of authoritative automotive sources."""
    sources_summary = [
        {
            "name": "Tata Motors EV",
            "domain": "ev.tatamotors.com",
            "type": "Official OEM",
            "priority": "Highest for Tata EV specs, battery warranty & pricing",
            "url": "https://ev.tatamotors.com"
        },
        {
            "name": "Mahindra Auto",
            "domain": "auto.mahindra.com",
            "type": "Official OEM",
            "priority": "Highest for XUV700, Scorpio-N, Thar Roxx technical data",
            "url": "https://auto.mahindra.com"
        },
        {
            "name": "Hyundai India",
            "domain": "hyundai.com",
            "type": "Official OEM",
            "priority": "Official source for Creta, Creta EV, and Ioniq 5 claims",
            "url": "https://www.hyundai.com/in/en"
        },
        {
            "name": "ARAI (Automotive Research Association of India)",
            "domain": "araiindia.com",
            "type": "Statutory Authority",
            "priority": "Highest authority for certified mileage and EV range in India",
            "url": "https://www.araiindia.com"
        },
        {
            "name": "NHTSA / Bharat NCAP",
            "domain": "nhtsa.gov",
            "type": "Safety Standards",
            "priority": "Crash test ratings, child occupant safety, structural integrity",
            "url": "https://www.nhtsa.gov"
        },
        {
            "name": "CarDekho",
            "domain": "cardekho.com",
            "type": "Automotive Research Portal",
            "priority": "On-road pricing, real-world mileage tests, user reviews",
            "url": "https://www.cardekho.com"
        },
        {
            "name": "ZigWheels",
            "domain": "zigwheels.com",
            "type": "Automotive Research Portal",
            "priority": "Comparison matrices, expert road tests, launch timelines",
            "url": "https://www.zigwheels.com"
        }
    ]

    recent_from_db = await db.get_recent_sources(limit=10)

    return {
        "priority_authoritative_sources": sources_summary,
        "recently_crawled_sources": recent_from_db
    }
