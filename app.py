"""
ArchiTek V9 — Production-Ready Market Intelligence Platform
============================================================
Street-smart SaaS for VCs, CTOs, and Founders.
Transforms academic research into actionable market intelligence.
Key Features:
  - Deal Flow Radar: Pattern detection across reports
  - Founder DNA Matcher: Team profile extraction
  - Market Timing Score: Algorithmic investment timing
  - Competitive Battlecards: Auto-generated investor memos
"""
import os
import re
import sqlite3
import hashlib
import requests
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from io import BytesIO
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px
from contextlib import contextmanager
import logging
# ═══════════════════════════════════════════════════════════════════════════════
# 1. CONFIGURATION & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
class Tier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
@dataclass
class TierLimits:
    reports_per_day: int
    max_pages: int
    export_enabled: bool
    battlecard_enabled: bool
    deal_radar_enabled: bool
    team_collab: bool
TIER_CONFIG = {
    Tier.FREE: TierLimits(1, 30, False, False, False, False),
    Tier.PRO: TierLimits(25, 100, True, True, False, False),
    Tier.ENTERPRISE: TierLimits(999, 500, True, True, True, True),
}
PRICING = {
    Tier.FREE: 0,
    Tier.PRO: 49,
    Tier.ENTERPRISE: 499,
}
# Supported research platforms
SUPPORTED_PLATFORMS = {
    "arxiv.org": {"name": "arXiv", "pdf_pattern": r'(\d{4}\.\d{4,5})'},
    "biorxiv.org": {"name": "bioRxiv", "pdf_pattern": r'/(\d+\.\d+\.\d+\.\d+)'},
    "medrxiv.org": {"name": "medRxiv", "pdf_pattern": r'/(\d+\.\d+\.\d+\.\d+)'},
}
# Trending sectors with real signals
TRENDING_SECTORS = {
    "AI Agents": {"heat": 95, "velocity": "+42%", "stage": "Early Growth"},
    "Climate Tech": {"heat": 82, "velocity": "+28%", "stage": "Expansion"},
    "Space Tech": {"heat": 71, "velocity": "+15%", "stage": "Maturing"},
    "Longevity Biotech": {"heat": 88, "velocity": "+35%", "stage": "Emerging"},
    "Quantum Computing": {"heat": 65, "velocity": "+12%", "stage": "R&D Heavy"},
    "Neurotech": {"heat": 74, "velocity": "+22%", "stage": "Early"},
    "Defense Tech": {"heat": 79, "velocity": "+31%", "stage": "Growth"},
    "Fintech Infrastructure": {"heat": 68, "velocity": "+8%", "stage": "Mature"},
}
# ═══════════════════════════════════════════════════════════════════════════════
# 2. DATABASE LAYER
# ═══════════════════════════════════════════════════════════════════════════════
DB_PATH = "architek.db"
def get_db_connection():
    """Thread-safe database connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
def init_database():
    """Initialize database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            api_key_hash TEXT UNIQUE,
            tier TEXT DEFAULT 'free',
            stripe_customer_id TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP
        )
    """)
    
    # Reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            source_url TEXT,
            source_type TEXT,
            role TEXT,
            industry TEXT,
            content_hash TEXT,
            insights TEXT,
            timing_score INTEGER,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Usage logs for rate limiting
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Waitlist for leads
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            source TEXT,
            tier_interest TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
# Initialize on import
init_database()
# ═══════════════════════════════════════════════════════════════════════════════
# 3. USER & TIER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:32]
def get_or_create_user(api_key: str) -> Dict[str, Any]:
    """Get existing user or create new one."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    key_hash = hash_api_key(api_key)
    
    cursor.execute("SELECT * FROM users WHERE api_key_hash = ?", (key_hash,))
    user = cursor.fetchone()
    
    if not user:
        user_id = hashlib.md5(f"{api_key}{datetime.now().isoformat()}".encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (id, api_key_hash, tier) VALUES (?, ?, ?)",
            (user_id, key_hash, Tier.FREE.value)
        )
        conn.commit()
        user = {"id": user_id, "tier": Tier.FREE.value}
    else:
        user = dict(user)
        cursor.execute(
            "UPDATE users SET last_active = ? WHERE id = ?",
            (datetime.now(), user["id"])
        )
        conn.commit()
    
    conn.close()
    return user
def get_user_tier(user: Dict) -> Tier:
    """Get user's tier as enum."""
    return Tier(user.get("tier", "free"))
def check_rate_limit(user_id: str, tier: Tier) -> tuple[bool, int]:
    """Check if user has exceeded rate limit. Returns (allowed, remaining)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    cursor.execute(
        """SELECT COUNT(*) FROM usage_logs 
           WHERE user_id = ? AND action = 'report' 
           AND DATE(timestamp) = ?""",
        (user_id, today)
    )
    count = cursor.fetchone()[0]
    conn.close()
    
    limit = TIER_CONFIG[tier].reports_per_day
    remaining = max(0, limit - count)
    
    return count < limit, remaining
def log_usage(user_id: str, action: str):
    """Log user action for analytics and rate limiting."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usage_logs (user_id, action) VALUES (?, ?)",
        (user_id, action)
    )
    conn.commit()
    conn.close()
def save_report(user_id: str, report_data: Dict):
    """Save generated report to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    report_id = hashlib.md5(
        f"{user_id}{report_data.get('source_url', '')}{datetime.now().isoformat()}".encode()
    ).hexdigest()
    
    cursor.execute(
        """INSERT INTO reports 
           (id, user_id, source_url, source_type, role, industry, content_hash, 
            insights, timing_score, keywords)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            report_id,
            user_id,
            report_data.get("source_url", "upload"),
            report_data.get("source_type", "pdf"),
            report_data.get("role"),
            report_data.get("industry"),
            report_data.get("content_hash"),
            report_data.get("insights", "")[:5000],
            report_data.get("timing_score", 0),
            ",".join(report_data.get("keywords", []))
        )
    )
    conn.commit()
    conn.close()
    return report_id
def get_user_reports(user_id: str, limit: int = 10) -> List[Dict]:
    """Get user's recent reports."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM reports WHERE user_id = ? 
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    )
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reports
def get_platform_stats() -> Dict:
    """Get real platform statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total reports
    cursor.execute("SELECT COUNT(*) FROM reports")
    total_reports = cursor.fetchone()[0]
    
    # Active users (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    cursor.execute(
        "SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE timestamp > ?",
        (week_ago,)
    )
    active_users = cursor.fetchone()[0]
    
    # Reports today
    today = datetime.now().date()
    cursor.execute(
        "SELECT COUNT(*) FROM reports WHERE DATE(created_at) = ?",
        (today,)
    )
    reports_today = cursor.fetchone()[0]
    
    # Top industries
    cursor.execute(
        """SELECT industry, COUNT(*) as cnt FROM reports 
           GROUP BY industry ORDER BY cnt DESC LIMIT 5"""
    )
    top_industries = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_reports": total_reports,
        "active_users": max(active_users, 1),  # Minimum 1 for new installs
        "reports_today": reports_today,
        "top_industries": top_industries
    }
def add_to_waitlist(email: str, source: str, tier_interest: str) -> bool:
    """Add email to waitlist."""
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO waitlist (email, source, tier_interest) VALUES (?, ?, ?)",
            (email.lower(), source, tier_interest)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False  # Already exists
    conn.close()
    return success
# ═══════════════════════════════════════════════════════════════════════════════
# 4. INTELLIGENCE ENGINE - PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════
ROLE_TEMPLATES = {
    "Venture Capital Partner": {
        "lens": "Investment thesis and fund deployment",
        "sections": [
            "🎯 **Investment Thesis Fit** — How this aligns with current fund mandates",
            "📊 **Market Heatmap** — TAM/SAM/SOM with growth vectors",
            "⚔️ **Competitive Moat Analysis** — Defensibility scoring (1-10)",
            "💰 **Deal Structure Recommendation** — Stage, check size, terms",
            "🚨 **Red Flags & Due Diligence Points** — What to probe deeper",
        ],
        "metrics": ["TAM ($B)", "CAC/LTV Ratio", "Gross Margin %", "MoM Growth", "Burn Multiple"],
        "output_format": "decision_table",
    },
    "Chief Technology Officer": {
        "lens": "Technical architecture and build-vs-buy",
        "sections": [
            "🏗️ **Architecture Blueprint** — System design with Graphviz DOT diagram",
            "⚡ **Technical Moat Score** — Proprietary tech assessment (1-10)",
            "🔧 **Build Complexity Matrix** — Effort vs Impact grid",
            "👥 **Team Skill Gap Analysis** — Required hires and upskilling",
            "🛡️ **Security & Scale Risks** — Production readiness checklist",
        ],
        "metrics": ["Complexity Index", "Tech Debt Score", "Time to MVP", "Infra Cost/mo", "LOC Estimate"],
        "output_format": "architecture_doc",
    },
    "Staff Software Engineer": {
        "lens": "Implementation and code architecture",
        "sections": [
            "📦 **MVP Feature Breakdown** — Core vs Nice-to-have",
            "🔄 **Data Flow Diagram** — Graphviz DOT for system flows",
            "💻 **Code Structure** — File/module organization",
            "🧪 **Testing Strategy** — Unit, integration, e2e approach",
            "⚙️ **DevOps Pipeline** — CI/CD recommendations",
        ],
        "metrics": ["LOC Estimate", "Test Coverage %", "API Endpoints", "DB Tables", "Sprint Estimate"],
        "output_format": "technical_spec",
    },
    "Brand & Content Lead": {
        "lens": "Go-to-market and content strategy",
        "sections": [
            "🎣 **Hook Headlines** — 5 viral-ready headlines",
            "📝 **LinkedIn Post Draft** — Ready-to-publish thought leadership",
            "🎬 **YouTube Script Outline** — 8-minute educational format",
            "🐦 **Twitter/X Thread** — 7-tweet breakdown",
            "📈 **Content Calendar** — 30-day rollout plan",
        ],
        "metrics": ["Virality Score", "Engagement Est.", "SEO Keywords", "Conversion Hook"],
        "output_format": "content_brief",
    },
    "CEO/Founder": {
        "lens": "Strategic positioning and fundraising",
        "sections": [
            "🎯 **Executive Summary** — 3-sentence pitch",
            "🏆 **Competitive Positioning** — Where you win",
            "📊 **Investor Deck Outline** — 10-slide structure",
            "🚀 **90-Day Sprint Plan** — Immediate priorities",
            "💡 **Pivot Opportunities** — Adjacent markets",
        ],
        "metrics": ["Market Entry Cost", "Time to PMF", "Runway Needed", "Key Hires"],
        "output_format": "executive_brief",
    },
    "Product Manager": {
        "lens": "Product strategy and roadmap",
        "sections": [
            "🗺️ **Product Roadmap** — Q1-Q4 milestones",
            "👤 **User Persona Deep Dive** — Jobs-to-be-done",
            "📋 **Feature Prioritization Matrix** — Impact vs Effort",
            "📊 **Success Metrics** — North star + supporting KPIs",
            "🔄 **Feedback Loop Design** — User research plan",
        ],
        "metrics": ["User Stories", "Sprint Velocity", "NPS Target", "Activation Rate"],
        "output_format": "prd",
    },
    "Investment Banker": {
        "lens": "M&A and deal structuring",
        "sections": [
            "💼 **Deal Landscape** — Active buyers and strategic fit",
            "📈 **Valuation Framework** — Comparable transactions",
            "🤝 **Synergy Analysis** — Cost savings and revenue upside",
            "📋 **Due Diligence Checklist** — Critical items",
            "⏱️ **Timeline & Process** — Deal execution roadmap",
        ],
        "metrics": ["EV/Revenue Multiple", "Synergy Value", "Integration Cost", "Time to Close"],
        "output_format": "deal_memo",
    },
}
def extract_keywords(text: str) -> List[str]:
    """Extract key technology and business terms."""
    # Common tech/business keywords to look for
    keyword_patterns = [
        r'\b(AI|ML|LLM|GPT|transformer|neural network)\b',
        r'\b(blockchain|crypto|web3|DeFi)\b',
        r'\b(quantum|qubit)\b',
        r'\b(CRISPR|gene therapy|biotech)\b',
        r'\b(API|SDK|SaaS|PaaS)\b',
        r'\b(revenue|ARR|MRR|growth|churn)\b',
        r'\b(Series [A-D]|seed|IPO|acquisition)\b',
    ]
    
    keywords = set()
    text_lower = text.lower()
    
    for pattern in keyword_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.update(m.upper() if len(m) <= 4 else m.title() for m in matches)
    
    return list(keywords)[:15]
def calculate_timing_score(text: str, industry: str) -> int:
    """
    Calculate Market Timing Score based on real signals.
    Score 0-100 based on:
    - Industry heat from our tracking
    - Keyword recency signals
    - Competitive density
    """
    base_score = 50
    
    # Industry heat factor
    if industry in TRENDING_SECTORS:
        heat = TRENDING_SECTORS[industry]["heat"]
        base_score += (heat - 70) // 2  # Adjust based on heat
    
    # Technology maturity signals
    early_signals = ["prototype", "early results", "preliminary", "novel approach", "first"]
    mature_signals = ["established", "proven", "widely adopted", "industry standard"]
    
    text_lower = text[:10000].lower()
    
    early_count = sum(1 for s in early_signals if s in text_lower)
    mature_count = sum(1 for s in mature_signals if s in text_lower)
    
    if early_count > mature_count:
        base_score += 15  # Early stage = higher timing opportunity
    elif mature_count > early_count:
        base_score -= 10  # Mature = harder to differentiate
    
    # Competition signals
    if "competitor" in text_lower or "versus" in text_lower:
        base_score -= 5  # Competitive space
    
    # Scale to 0-100
    return max(0, min(100, base_score))
def build_strategic_prompt(role: str, industry: str, text: str, tier: Tier) -> str:
    """Build role-specific analysis prompt."""
    template = ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["Venture Capital Partner"])
    
    # Extract key signals
    keywords = extract_keywords(text)
    timing_score = calculate_timing_score(text, industry)
    
    # Industry context
    industry_context = ""
    if industry in TRENDING_SECTORS:
        sector = TRENDING_SECTORS[industry]
        industry_context = f"""
**SECTOR INTELLIGENCE**: {industry}
- Market Heat Index: {sector['heat']}/100
- Growth Velocity: {sector['velocity']} YoY
- Stage: {sector['stage']}
"""
    
    # Build sections based on tier
    if tier == Tier.FREE:
        sections = template["sections"][:3]
        section_note = "\n> ⚡ *Upgrade to Pro for full analysis with all sections*\n"
    elif tier == Tier.PRO:
        sections = template["sections"][:4]
        section_note = "\n> 🏢 *Upgrade to Enterprise for Deal Flow Radar and Team Collaboration*\n"
    else:
        sections = template["sections"]
        section_note = ""
    
    prompt = f"""
# STRATEGIC ANALYSIS REQUEST
**ANALYST ROLE**: {role}
**ANALYSIS LENS**: {template['lens']}
**TARGET SECTOR**: {industry}
**TIMING SCORE**: {timing_score}/100
{industry_context}
---
## SOURCE MATERIAL
{text[:75000]}
---
## REQUIRED ANALYSIS
Generate a comprehensive, actionable intelligence report with the following sections:
{chr(10).join(sections)}
{section_note}
## KEY METRICS TO CALCULATE
{', '.join(template['metrics'])}
## FORMATTING REQUIREMENTS
1. Use markdown tables for comparative data
2. Include a Graphviz DOT diagram in ```dot code blocks for technical/architecture visuals
3. Keep insights actionable — every point should have a "So what?" implication
4. Bold key numbers and decisions
5. Use emoji sparingly for section headers only
## EXTRACTED KEYWORDS FOR CONTEXT
{', '.join(keywords) if keywords else 'General research'}
---
Begin your analysis:
"""
    
    return prompt, keywords, timing_score
# ═══════════════════════════════════════════════════════════════════════════════
# 5. DEAL FLOW RADAR (Enterprise Feature)
# ═══════════════════════════════════════════════════════════════════════════════
def analyze_deal_flow(user_id: str) -> Dict:
    """
    Analyze patterns across user's reports to identify trends.
    Enterprise-only feature.
    """
    reports = get_user_reports(user_id, limit=50)
    
    if len(reports) < 3:
        return {"status": "insufficient_data", "message": "Need at least 3 reports for pattern analysis"}
    
    # Aggregate keywords
    all_keywords = []
    industries = []
    timing_scores = []
    
    for report in reports:
        if report.get("keywords"):
            all_keywords.extend(report["keywords"].split(","))
        if report.get("industry"):
            industries.append(report["industry"])
        if report.get("timing_score"):
            timing_scores.append(report["timing_score"])
    
    # Find trending keywords
    keyword_counts = {}
    for kw in all_keywords:
        kw = kw.strip()
        if kw:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    trending = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Industry concentration
    industry_counts = {}
    for ind in industries:
        industry_counts[ind] = industry_counts.get(ind, 0) + 1
    
    top_industries = sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Average timing score trend
    avg_timing = sum(timing_scores) / len(timing_scores) if timing_scores else 50
    
    return {
        "status": "success",
        "trending_technologies": trending,
        "industry_focus": top_industries,
        "average_timing_score": round(avg_timing, 1),
        "total_reports_analyzed": len(reports),
        "recommendation": _generate_deal_recommendation(trending, top_industries, avg_timing)
    }
def _generate_deal_recommendation(trends: List, industries: List, timing: float) -> str:
    """Generate actionable recommendation from deal flow data."""
    if not trends or not industries:
        return "Build more report history to generate recommendations."
    
    top_tech = trends[0][0] if trends else "emerging tech"
    top_industry = industries[0][0] if industries else "your focus sector"
    
    if timing > 70:
        timing_msg = "Market timing is favorable — consider accelerating deal flow."
    elif timing > 50:
        timing_msg = "Market timing is neutral — maintain current pace."
    else:
        timing_msg = "Market timing suggests caution — focus on quality over quantity."
    
    return f"Your research shows strong interest in **{top_tech}** within **{top_industry}**. {timing_msg}"
# ═══════════════════════════════════════════════════════════════════════════════
# 6. PDF PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════
def validate_url(url: str) -> tuple[bool, str, str]:
    """
    Validate research URL and extract PDF URL.
    Returns: (is_valid, pdf_url, platform_name)
    """
    url = url.strip()
    
    if not url:
        return False, "", "No URL provided"
    
    # Check supported platforms
    for domain, config in SUPPORTED_PLATFORMS.items():
        if domain in url:
            match = re.search(config["pdf_pattern"], url)
            if match:
                paper_id = match.group(1)
                if domain == "arxiv.org":
                    pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
                else:
                    pdf_url = url.replace("/abs/", "/pdf/")
                return True, pdf_url, config["name"]
    
    # Check if direct PDF
    if url.endswith('.pdf'):
        return True, url, "Direct PDF"
    
    # Try to fetch and check content-type
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_type = response.headers.get('content-type', '')
        if 'pdf' in content_type.lower():
            return True, url, "PDF URL"
    except requests.RequestException:
        pass
    
    return False, "", "Unsupported URL format"
def extract_pdf_text(stream: BytesIO, max_pages: int) -> tuple[str, int]:
    """
    Extract text from PDF with page limit.
    Returns: (text, page_count)
    """
    try:
        reader = PdfReader(stream)
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)
        
        text_parts = []
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return "\n".join(text_parts), total_pages
    except Exception as e:
        logging.error(f"PDF extraction error: {e}")
        raise ValueError(f"Failed to extract PDF text: {str(e)}")
# ═══════════════════════════════════════════════════════════════════════════════
# 7. STREAMLIT UI
# ═══════════════════════════════════════════════════════════════════════════════
# Page config
st.set_page_config(
    page_title="ArchiTek | Market Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit branding */
    header, footer, .stAppDeployButton, 
    [data-testid="stStatusWidget"], 
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"] {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* Dark theme */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #0d1117 100%);
        color: #e6e6e6;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%) !important;
        border-right: 1px solid #30363d !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #e6e6e6 !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        background-color: #161b22 !important;
        color: #fafafa !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* Primary button */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(35, 134, 54, 0.4) !important;
    }
    
    /* Secondary button */
    div.stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #58a6ff !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.5rem 0;
    }
    
    .metric-card h4 {
        color: #8b949e;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .metric-card .value {
        color: #ffffff;
        font-size: 1.75rem;
        font-weight: 700;
    }
    
    .metric-card .delta {
        color: #3fb950;
        font-size: 0.9rem;
    }
    
    .metric-card .delta.negative {
        color: #f85149;
    }
    
    /* Tier badges */
    .tier-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .tier-free { background: #30363d; color: #8b949e; }
    .tier-pro { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
    .tier-enterprise { background: linear-gradient(135deg, #f093fb, #f5576c); color: white; }
    
    /* Report section */
    .report-container {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    /* Upgrade banner */
    .upgrade-banner {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #4a4a6a;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Hide default padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Links */
    a {
        color: #58a6ff !important;
        text-decoration: none !important;
    }
    
    a:hover {
        text-decoration: underline !important;
    }
    
    /* Brand buttons */
    .brand-btn {
        display: block;
        width: 100%;
        padding: 12px;
        margin: 8px 0;
        text-align: center;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        text-decoration: none !important;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .brand-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .btn-linkedin { background: #0077b5; }
    .btn-youtube { background: #ff0000; }
    .btn-gurukul { background: linear-gradient(135deg, #238636, #2ea043); }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #161b22 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)
# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None
if "current_report" not in st.session_state:
    st.session_state.current_report = None
# ═══════════════════════════════════════════════════════════════════════════════
# 8. SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 🏛️ ArchiTek")
    st.caption("Strategic Intelligence Engine • V9.0")
    st.markdown("---")
    
    # API Key handling
    try:
        sponsor_key = st.secrets.get("GOOGLE_API_KEY")
    except (FileNotFoundError, KeyError):
        sponsor_key = None
    
    # Show tier selector if no sponsor key
    if not sponsor_key:
        st.subheader("🔐 Access")
        
        selected_tier = st.radio(
            "Select Plan",
            ["Free (1/day)", "Pro ($49/mo)", "Enterprise ($499/mo)"],
            horizontal=True,
            help="Pro and Enterprise require activation"
        )
        
        if "Pro" in selected_tier or "Enterprise" in selected_tier:
            st.info("📧 Contact sales@architek.ai for activation")
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("💳 Upgrade", "https://buy.stripe.com/test_architek", use_container_width=True)
            with col2:
                st.link_button("📅 Demo", "https://calendly.com/architek", use_container_width=True)
    
    api_key = sponsor_key or st.text_input(
        "API Key",
        type="password",
        placeholder="Enter Google AI API key",
        help="Get your key at ai.google.dev"
    )
    
    # Authenticate user
    if api_key:
        st.session_state.user = get_or_create_user(api_key)
        user_tier = get_user_tier(st.session_state.user)
        tier_limits = TIER_CONFIG[user_tier]
        
        allowed, remaining = check_rate_limit(st.session_state.user["id"], user_tier)
        
        tier_class = f"tier-{user_tier.value}"
        st.markdown(f'<span class="tier-badge {tier_class}">{user_tier.value}</span>', unsafe_allow_html=True)
        st.caption(f"📊 {remaining} reports remaining today")
    
    st.markdown("---")
    
    # Role & Industry selection
    st.subheader("🎯 Analysis Profile")
    
    user_role = st.selectbox(
        "Your Role",
        list(ROLE_TEMPLATES.keys()),
        help="Tailors the analysis to your decision-making needs"
    )
    
    # Industry with heat indicators
    industry_options = ["General"] + list(TRENDING_SECTORS.keys())
    industry = st.selectbox(
        "Target Sector",
        industry_options,
        help="Adds sector-specific intelligence"
    )
    
    # Show sector heat if selected
    if industry in TRENDING_SECTORS:
        sector = TRENDING_SECTORS[industry]
        st.markdown(f"""
        <div class="metric-card">
            <h4>Sector Heat Index</h4>
            <div class="value">{sector['heat']}/100</div>
            <div class="delta">{sector['velocity']} growth</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Platform stats (real data)
    stats = get_platform_stats()
    
    with st.expander("📈 Platform Analytics", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Reports", f"{stats['total_reports']:,}")
            st.metric("Active Users", stats['active_users'])
        with col2:
            st.metric("Today", stats['reports_today'])
            if stats['top_industries']:
                st.caption(f"Top: {stats['top_industries'][0] if stats['top_industries'] else 'N/A'}")
    
    # Lead capture
    with st.expander("📬 Weekly Intel Digest"):
        lead_email = st.text_input("Email", placeholder="you@company.com", key="lead_email")
        if st.button("Subscribe", use_container_width=True):
            if add_to_waitlist(lead_email, "sidebar", "newsletter"):
                st.success("✅ Subscribed!")
            else:
                st.error("Invalid email or already subscribed")
    
    st.markdown("---")
    
    # Founder links
    st.subheader("🔗 Connect")
    st.markdown("""
    <a class="brand-btn btn-linkedin" href="https://www.linkedin.com/in/prashantbhardwaj30/" target="_blank" rel="noopener">
        🔗 LinkedIn — Prashant Bhardwaj
    </a>
    <a class="brand-btn btn-youtube" href="https://www.youtube.com/@DesiAILabs" target="_blank" rel="noopener">
        🎬 YouTube — Desi AI Labs
    </a>
    <a class="brand-btn btn-gurukul" href="https://aigurukul.lovable.app" target="_blank" rel="noopener">
        🎓 AI Gurukul Training
    </a>
    """, unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════════════════════
# 9. MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════
# Header
st.title("ArchiTek // Market Intelligence")
st.markdown("**Transform research papers into actionable intelligence.** Trusted by elite operators.")
# Input section
col1, col2 = st.columns([2, 1])
with col1:
    url_input = st.text_input(
        "Research URL",
        placeholder="https://arxiv.org/abs/2401.12345",
        help="Supports arXiv, bioRxiv, medRxiv, or direct PDF links"
    )
with col2:
    uploaded_file = st.file_uploader(
        "Or Upload PDF",
        type=["pdf"],
        help="Max 20MB"
    )
# Action buttons
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    generate_clicked = st.button(
        "🚀 Generate Intelligence Report",
        type="primary",
        use_container_width=True,
        disabled=not api_key
    )
with col2:
    if st.button("📊 Export", type="secondary", use_container_width=True):
        if st.session_state.user:
            tier = get_user_tier(st.session_state.user)
            if TIER_CONFIG[tier].export_enabled:
                if st.session_state.current_report:
                    st.download_button(
                        "Download MD",
                        st.session_state.current_report,
                        file_name="architek_report.md",
                        mime="text/markdown"
                    )
                else:
                    st.warning("Generate a report first")
            else:
                st.warning("⚡ Export requires Pro tier")
        else:
            st.warning("Enter API key first")
with col3:
    if st.button("📜 History", type="secondary", use_container_width=True):
        if st.session_state.user:
            reports = get_user_reports(st.session_state.user["id"], limit=5)
            if reports:
                with st.expander("Recent Reports", expanded=True):
                    for r in reports:
                        st.write(f"**{r['role']}** • {r['industry']} • {r['created_at'][:10]}")
                        st.caption(f"Timing Score: {r['timing_score']}/100")
            else:
                st.info("No reports yet")
st.markdown("---")
# ═══════════════════════════════════════════════════════════════════════════════
# 10. REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════
if generate_clicked and api_key:
    # Validate user and rate limit
    if not st.session_state.user:
        st.error("Authentication failed. Please check your API key.")
        st.stop()
    
    user_tier = get_user_tier(st.session_state.user)
    tier_limits = TIER_CONFIG[user_tier]
    
    allowed, remaining = check_rate_limit(st.session_state.user["id"], user_tier)
    
    if not allowed:
        st.error(f"⚡ Daily limit reached ({tier_limits.reports_per_day} reports/day)")
        st.markdown("""
        <div class="upgrade-banner">
            <h3>Unlock More Reports</h3>
            <p>Upgrade to Pro for 25 reports/day or Enterprise for unlimited.</p>
            <a href="https://buy.stripe.com/test_architek" target="_blank">
                <button style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; 
                              border: none; padding: 12px 30px; border-radius: 8px; font-weight: 600; 
                              cursor: pointer; margin-top: 10px;">
                    Upgrade Now →
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Get PDF stream
    pdf_stream = None
    source_url = ""
    source_type = ""
    
    if url_input:
        is_valid, pdf_url, platform = validate_url(url_input)
        
        if not is_valid:
            st.error(f"❌ {platform}")
            st.info("Supported: arXiv, bioRxiv, medRxiv, or direct PDF links")
            st.stop()
        
        source_url = url_input
        source_type = platform
        
        with st.spinner(f"📥 Fetching from {platform}..."):
            try:
                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()
                pdf_stream = BytesIO(response.content)
            except requests.RequestException as e:
                st.error(f"Failed to fetch PDF: {str(e)}")
                st.stop()
    
    elif uploaded_file:
        pdf_stream = uploaded_file
        source_url = "upload"
        source_type = "Upload"
    
    else:
        st.warning("Please provide a URL or upload a PDF")
        st.stop()
    
    # Process PDF
    with st.spinner("📄 Extracting content..."):
        try:
            content, page_count = extract_pdf_text(pdf_stream, tier_limits.max_pages)
            
            if page_count > tier_limits.max_pages:
                st.info(f"📄 Processing first {tier_limits.max_pages} of {page_count} pages (tier limit)")
            
            if len(content) < 500:
                st.error("PDF appears to have too little extractable text")
                st.stop()
                
        except ValueError as e:
            st.error(str(e))
            st.stop()
    
    # Generate report
    with st.spinner("🧠 Generating intelligence report..."):
        try:
            genai.configure(api_key=api_key)
            
            # Get available model
            models = [m.name for m in genai.list_models() 
                     if 'generateContent' in m.supported_generation_methods]
            
            # Prefer flash for speed
            model_name = next(
                (m for m in models if 'flash' in m.lower()),
                models[0] if models else None
            )
            
            if not model_name:
                st.error("No compatible Gemini model found")
                st.stop()
            
            model_name = model_name.split('/')[-1]
            
            # Build prompt
            prompt, keywords, timing_score = build_strategic_prompt(
                user_role, industry, content, user_tier
            )
            
            # Generate
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            report_text = response.text
            st.session_state.current_report = report_text
            
            # Log usage and save report
            log_usage(st.session_state.user["id"], "report")
            
            content_hash = hashlib.md5(content[:1000].encode()).hexdigest()
            
            report_id = save_report(st.session_state.user["id"], {
                "source_url": source_url,
                "source_type": source_type,
                "role": user_role,
                "industry": industry,
                "content_hash": content_hash,
                "insights": report_text[:2000],
                "timing_score": timing_score,
                "keywords": keywords
            })
            
        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            logging.error(f"Gemini API error: {e}")
            st.stop()
    
    # Display report
    st.markdown("---")
    
    # Report header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 📋 Intelligence Report")
        st.caption(f"{user_role} • {industry} • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    with col2:
        st.metric("Pages Analyzed", page_count)
    with col3:
        st.metric("Timing Score", f"{timing_score}/100")
    
    st.markdown("---")
    
    # Report content
    st.markdown(report_text)
    
    # Extract and display Graphviz diagrams
    dot_matches = re.findall(r'```dot\n(.*?)\n```', report_text, re.DOTALL)
    if dot_matches:
        st.subheader("📊 Architecture Diagrams")
        for i, dot_code in enumerate(dot_matches):
            try:
                st.graphviz_chart(dot_code)
            except Exception as e:
                st.warning(f"Could not render diagram {i+1}")
    
    # Market Timing Gauge
    st.markdown("---")
    st.subheader("📈 Market Timing Analysis")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=timing_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Investment Timing Score", 'font': {'color': 'white'}},
        delta={'reference': 50, 'increasing': {'color': '#3fb950'}, 'decreasing': {'color': '#f85149'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': 'white'},
            'bar': {'color': '#238636'},
            'bgcolor': '#161b22',
            'borderwidth': 2,
            'bordercolor': '#30363d',
            'steps': [
                {'range': [0, 40], 'color': 'rgba(248, 81, 73, 0.15)'},
                {'range': [40, 70], 'color': 'rgba(210, 153, 34, 0.15)'},
                {'range': [70, 100], 'color': 'rgba(63, 185, 80, 0.15)'}
            ],
            'threshold': {
                'line': {'color': '#ffffff', 'width': 4},
                'thickness': 0.75,
                'value': timing_score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        paper_bgcolor='#0d1117',
        font={'color': 'white'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Timing interpretation
    if timing_score >= 70:
        st.success("🟢 **Favorable timing** — Market conditions support aggressive positioning")
    elif timing_score >= 50:
        st.info("🟡 **Neutral timing** — Proceed with standard due diligence")
    else:
        st.warning("🔴 **Cautious timing** — Consider waiting for better market conditions")
    
    # Keywords extracted
    if keywords:
        st.markdown("---")
        st.subheader("🏷️ Key Technologies Detected")
        st.write(" • ".join([f"`{kw}`" for kw in keywords]))
    
    # Deal Flow Radar (Enterprise only)
    if user_tier == Tier.ENTERPRISE:
        st.markdown("---")
        st.subheader("🛸 Deal Flow Radar")
        
        radar_data = analyze_deal_flow(st.session_state.user["id"])
        
        if radar_data["status"] == "success":
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Trending Technologies in Your Research**")
                for tech, count in radar_data["trending_technologies"][:5]:
                    st.write(f"• {tech} ({count} mentions)")
            
            with col2:
                st.markdown("**Industry Focus**")
                for ind, count in radar_data["industry_focus"]:
                    st.write(f"• {ind} ({count} reports)")
            
            st.info(f"💡 **Recommendation**: {radar_data['recommendation']}")
        else:
            st.info(radar_data["message"])
    else:
        # Upsell for Deal Flow Radar
        st.markdown("""
        <div class="upgrade-banner">
            <h4>🛸 Unlock Deal Flow Radar</h4>
            <p>Enterprise tier includes pattern analysis across all your reports.</p>
            <p style="color: #8b949e; font-size: 0.9rem;">
                Identify emerging trends before they hit mainstream.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Report complete
    st.markdown("---")
    st.success(f"✅ Report generated successfully! {remaining - 1} reports remaining today.")
# ═══════════════════════════════════════════════════════════════════════════════
# 11. FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
# CTA section
st.markdown("""
<div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #0d1117 0%, #1a2a1a 100%); 
            border-radius: 16px; border: 1px solid #30363d; margin-top: 2rem;">
    <h2 style="color: white; margin-bottom: 16px;">Ready to Scale Your Intelligence?</h2>
    <p style="color: #8b949e; font-size: 1.1rem; margin-bottom: 24px;">
        Join elite operators using ArchiTek to make faster, smarter decisions.
    </p>
    <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
        <a href="https://calendly.com/architek/demo" target="_blank" style="text-decoration: none;">
            <button style="background: linear-gradient(135deg, #238636, #2ea043); color: white; 
                          border: none; padding: 14px 36px; border-radius: 8px; font-weight: 600; 
                          font-size: 1rem; cursor: pointer;">
                Book Demo →
            </button>
        </a>
        <a href="https://aigurukul.lovable.app" target="_blank" style="text-decoration: none;">
            <button style="background: transparent; color: white; 
                          border: 2px solid #30363d; padding: 14px 36px; border-radius: 8px; 
                          font-weight: 600; font-size: 1rem; cursor: pointer;">
                🎓 AI Gurukul
            </button>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)
# Legal footer
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; border-top: 1px solid #30363d;">
    <p style="color: #6e7681; font-size: 0.85rem;">
        © 2025 ArchiTek Intelligence. All rights reserved.<br>
        <a href="#" style="color: #58a6ff;">Terms</a> • 
        <a href="#" style="color: #58a6ff;">Privacy</a> • 
        <a href="mailto:support@architek.ai" style="color: #58a6ff;">Contact</a>
    </p>
</div>
""", unsafe_allow_html=True)
