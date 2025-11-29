from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class RowMetrics(BaseModel):
    campaign_name: str
    adset_name: str
    date: str
    spend: float
    impressions: float
    clicks: float
    ctr: float
    purchases: float
    revenue: float
    roas: float
    creative_type: str
    creative_message: str
    audience_type: str
    platform: str
    country: str


class ROASSummary(BaseModel):
    baseline_roas: float
    recent_roas: float
    pct_change: float
    baseline_date_range: str
    recent_date_range: str


class InsightHypothesis(BaseModel):
    id: str
    title: str
    description: str
    driver_type: str
    expected_pattern: str
    confidence_model: float
    status: str = "pending"


class InsightEvidence(BaseModel):
    metric: str
    direction: str
    magnitude_pct: float
    details: str


class ValidatedInsight(BaseModel):
    hypothesis: InsightHypothesis
    evidence: List[InsightEvidence]
    quantitative_confidence: float
    final_confidence: float
    verdict: str


class CreativeIdea(BaseModel):
    campaign_name: str
    adset_name: str
    audience_type: str
    platform: str
    country: str
    current_ctr: float
    problem_statement: str
    new_headlines: List[str]
    new_primary_texts: List[str]
    new_ctas: List[str]


class InsightsReport(BaseModel):
    query: str
    roas_summary: ROASSummary
    top_insights: List[ValidatedInsight]


class CreativesReport(BaseModel):
    query: str
    ideas: List[CreativeIdea]
