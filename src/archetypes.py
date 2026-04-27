"""
Archetype Registry for Radius AI v9.
Defines the mapping between strategic slide topics and specialized UI components.
"""
from enum import Enum
from typing import List, Dict, Any

class SlideArchetype(Enum):
    TITLE = "title_v9"
    # V14 Mappings
    FUNNEL = "funnel_v14"
    ARCHITECTURE = "architecture_v14"
    COMPARISON = "comparison_v14"
    CHART = "metric_chart_v14"
    # Legacy fallbacks
    EXECUTIVE_SUMMARY = "exec_summary_v9"
    GEO_LOCAL_INSIGHT = "geo_local_v9"
    TECHNICAL_AUDIT = "technical_audit_v9"

# Mapping logic for V14
ARCHETYPE_RULES = {
    "AEO": SlideArchetype.FUNNEL,
    "Architecture": SlideArchetype.ARCHITECTURE,
    "Strategy": SlideArchetype.ARCHITECTURE,
    "Comparison": SlideArchetype.COMPARISON,
    "Maturity": SlideArchetype.COMPARISON,
    "Audit": SlideArchetype.CHART,
    "Metrics": SlideArchetype.CHART,
    "SEO Foundation": SlideArchetype.ARCHITECTURE,
    "GEO": SlideArchetype.GEO_LOCAL_INSIGHT,
    "Executive": SlideArchetype.EXECUTIVE_SUMMARY,
    "Roadmap": SlideArchetype.ARCHITECTURE
}

def get_archetype(title: str) -> str:
    for key, archetype in ARCHETYPE_RULES.items():
        if key.lower() in title.lower():
            return archetype.value
    return "generic_v9"
