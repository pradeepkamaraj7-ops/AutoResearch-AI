from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="The automotive research query")

class SourceItem(BaseModel):
    title: str = Field(..., description="Webpage or document title")
    url: str = Field(..., description="Direct URL of the verified source")
    domain: str = Field(..., description="Domain name of the source")
    relevance: str = Field("High", description="Relevance assessment or score")
    evidence: str = Field(..., description="Extracted evidence or snippet backing the facts")
    is_official: bool = Field(False, description="True if from an official OEM, ARAI, or NHTSA")

class SpecificationItem(BaseModel):
    category: str = Field("General", description="Category like Powertrain, Battery, Safety, Price")
    property: str = Field(..., description="Specification name e.g. Battery Capacity, ARAI Range")
    value: str = Field(..., description="Specification value e.g. 40.5 kWh, 465 km")
    unit: Optional[str] = Field(None, description="Optional measurement unit")
    source: Optional[str] = Field(None, description="Source domain or entity")

class ComparisonRow(BaseModel):
    feature: str = Field(..., description="Feature/attribute compared e.g. Price, Battery, Range")
    values: Dict[str, str] = Field(default_factory=dict, description="Mapping of vehicle name to spec value")
    has_conflict: bool = Field(False, description="Whether sources reported conflicting values")
    conflict_notes: Optional[str] = Field(None, description="Notes on source discrepancy if conflicting")

class ComparisonData(BaseModel):
    vehicles: List[str] = Field(default_factory=list, description="List of vehicles compared")
    rows: List[ComparisonRow] = Field(default_factory=list, description="Attribute comparison rows")
    conflicts_detected: bool = Field(False, description="True if conflicting information was found")
    summary: Optional[str] = Field(None, description="Quick verdict or comparative summary")

class ResearchResponse(BaseModel):
    success: bool = Field(True, description="Indicates if the research request was successful")
    query: str = Field(..., description="Original user query")
    query_type: str = Field("General Automotive", description="Detected query category")
    vehicles: List[str] = Field(default_factory=list, description="Detected vehicle entities")
    summary: str = Field(..., description="Concise executive summary of findings")
    answer: str = Field(..., description="Full synthesized answer with context and details")
    specifications: List[SpecificationItem] = Field(default_factory=list, description="Extracted key specifications")
    comparison: Optional[ComparisonData] = Field(None, description="Structured comparison table if applicable")
    key_findings: List[str] = Field(default_factory=list, description="Bulleted takeaway evidence points")
    sources: List[SourceItem] = Field(default_factory=list, description="Verified source citations")
    execution_time_seconds: float = Field(0.0, description="Pipeline latency in seconds")
    cached: bool = Field(False, description="Whether returned from database cache")
    note: Optional[str] = Field(None, description="Informational message, e.g. simulated fallback mode")
    deep_thinking_analysis: Optional[str] = Field(None, description="Deep engineering reasoning and technical breakdown")

class CompareRequest(BaseModel):
    vehicles: List[str] = Field(..., min_items=2, max_items=4, description="List of 2-4 vehicle names to compare")
    features: Optional[List[str]] = Field(None, description="Optional custom features to compare")

class HistoryItem(BaseModel):
    id: int
    query: str
    query_type: str
    summary: str
    created_at: str
    vehicles: List[str]

class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    crawl4ai_available: bool
    db_connected: bool
    version: str
    timestamp: str

class VehicleSpecResponse(BaseModel):
    vehicle_name: str
    specifications: List[SpecificationItem]
    sources: List[SourceItem]
    last_updated: Optional[str] = None

class VehicleReportRequest(BaseModel):
    vehicle_name: str = Field(..., min_length=2, max_length=150, description="Vehicle model to generate full dossier report for")

class VehicleReportResponse(BaseModel):
    success: bool = Field(True)
    vehicle_name: str
    tagline: str
    overview: str
    specifications: List[SpecificationItem]
    pros: List[str]
    cons: List[str]
    powertrain_analysis: str
    safety_and_chassis: str
    ownership_and_maintenance: str
    deep_engineering_verdict: str
    sources: List[SourceItem]
    generated_at: str
