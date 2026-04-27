#!/usr/bin/env python3
"""
Prospect Audit & Strategy — Phase 2: Multi-Layer Market & Competitive Intelligence
(SEO + GEO + AEO)
==================================================================================
Uses the SEMrush MCP server to gather essential market and competitor data,
plus AEO/GEO opportunity indicators.

This script is a TEMPLATE/GUIDE. The agent executes the SEMrush MCP calls
directly via manus-mcp-cli and saves the results to market_intelligence.json.

BUDGET: ~10,000-15,000 SEMrush API units per run.
"""

import json
import os

# ══════════════════════════════════════════════════════════════
# OUTPUT SCHEMA — The agent must populate this structure
# ══════════════════════════════════════════════════════════════

market_intelligence = {
    # ── Prospect Domain Metrics (SEO) ─────────────────────
    "prospect": {
        "domain": "",
        "authority_score": 0,
        "organic_keywords": 0,
        "organic_traffic": 0,
        "organic_traffic_value": 0,
        "backlinks": 0,
        "referring_domains": 0,
        "top_keywords": [],       # Top 20 keywords by traffic
    },

    # ── Competitor Data (SEO) ─────────────────────────────
    "competitors": [],            # List of competitor dicts (same structure as prospect)

    # ── Competitive Comparison Table ──────────────────────
    "comparison_table": [],       # List of dicts for easy table rendering

    # ── Backlink Overview (SEO) ───────────────────────────
    "backlink_overview": {
        "total_backlinks": 0,
        "referring_domains": 0,
        "follow_vs_nofollow": "",
        "top_anchors": [],
    },

    # ── AEO Opportunity Indicators ────────────────────────
    "aeo_indicators": {
        "question_keywords_found": 0,     # Total question-based keywords found
        "top_question_keywords": [],      # Top 20 question keywords by volume
        "featured_snippet_opportunities": [],  # Keywords where prospect could win snippets
        "paa_opportunities": [],          # People Also Ask opportunities
    },

    # ── GEO Opportunity Indicators ────────────────────────
    "geo_indicators": {
        "informational_keywords_found": 0,    # Total informational keywords found
        "top_informational_keywords": [],     # Top 20 informational keywords by volume
        "entity_strength_assessment": "",     # "Weak", "Moderate", "Strong"
        "competitor_entity_comparison": [],   # How competitors compare on entity signals
    },
}

# ══════════════════════════════════════════════════════════════
# SEMRUSH MCP CALL SEQUENCE (Budget: ~10,000-15,000 units)
# ══════════════════════════════════════════════════════════════

"""
The agent should execute these calls in order using manus-mcp-cli:

═══════════════════════════════════════════════════════════════
SECTION A: CORE SEO INTELLIGENCE (~5,000-8,000 units)
═══════════════════════════════════════════════════════════════

CALL 1: Domain Overview for Prospect (~500 units)
─────────────────────────────────────────────────
manus-mcp-cli tool call semrush_domain_ranks --server semrush-mcp-v2 --input '{
    "domain": "{{PROSPECT_DOMAIN}}",
    "database": "au"
}'

Extract: authority_score, organic_keywords, organic_traffic, organic_traffic_cost

CALL 2: Prospect's Top Organic Keywords (~2,000 units)
──────────────────────────────────────────────────────
manus-mcp-cli tool call semrush_domain_organic --server semrush-mcp-v2 --input '{
    "domain": "{{PROSPECT_DOMAIN}}",
    "database": "au",
    "display_limit": 200
}'

Extract: Top 200 keywords with position, volume, traffic, URL

CALL 3: Find Organic Competitors (~1,000 units)
────────────────────────────────────────────────
manus-mcp-cli tool call semrush_domain_organic_organic --server semrush-mcp-v2 --input '{
    "domain": "{{PROSPECT_DOMAIN}}",
    "database": "au",
    "display_limit": 10
}'

Extract: Top 5-10 organic competitors with overlap data

CALLS 4-8: Domain Overview for Each Competitor (~500 units each)
──────────────────────────────────────────────────────────────
For each of the top 3-5 competitors:
manus-mcp-cli tool call semrush_domain_ranks --server semrush-mcp-v2 --input '{
    "domain": "{{COMPETITOR_DOMAIN}}",
    "database": "au"
}'

CALL 9: Backlink Overview for Prospect (~500 units)
───────────────────────────────────────────────────
manus-mcp-cli tool call semrush_backlinks_overview --server semrush-mcp-v2 --input '{
    "target": "{{PROSPECT_DOMAIN}}",
    "target_type": "root_domain"
}'

═══════════════════════════════════════════════════════════════
SECTION B: AEO & GEO OPPORTUNITY INTELLIGENCE (~3,000-5,000 units)
═══════════════════════════════════════════════════════════════

CALLS 10-12: Question Keywords for Top 3 Non-Branded Seeds (~1,500 units)
────────────────────────────────────────────────────────────────────────
For each of the top 3 non-branded seed keywords from business_analysis.json:
manus-mcp-cli tool call semrush_phrase_questions --server semrush-mcp-v2 --input '{
    "phrase": "{{SEED_KEYWORD}}",
    "database": "au",
    "display_limit": 30
}'

Extract: Question-based keywords (how, what, why, where, when, which, can, does)
These feed the AEO opportunity analysis.

CALLS 13-15: Related Keywords for Top 3 Seeds (~1,500 units)
──────────────────────────────────────────────────────────
For each of the top 3 non-branded seed keywords:
manus-mcp-cli tool call semrush_phrase_related --server semrush-mcp-v2 --input '{
    "phrase": "{{SEED_KEYWORD}}",
    "database": "au",
    "display_limit": 50
}'

Extract: Related keywords including informational/conversational queries
These feed the GEO opportunity analysis.

TOTAL ESTIMATED BUDGET: 10,000 - 15,000 units
"""

# ══════════════════════════════════════════════════════════════
# POST-PROCESSING INSTRUCTIONS
# ══════════════════════════════════════════════════════════════

"""
After all calls are complete, the agent should:

1. Parse the semicolon-delimited output from each SEMrush call.

2. Populate the core SEO sections (prospect, competitors, comparison_table, backlinks).

3. Build the comparison_table as a list of dicts:
   [
       {"name": "Prospect", "keywords": 150, "traffic": 200, ...},
       {"name": "Competitor A", "keywords": 1200, "traffic": 3000, ...},
   ]

4. Process AEO indicators:
   - Count total question keywords found.
   - Identify top 20 question keywords by volume.
   - Flag keywords where the prospect doesn't rank but competitors do (snippet opportunities).

5. Process GEO indicators:
   - From the related keywords, identify informational/conversational queries
     (keywords with informational intent, long-tail queries, "best", "vs", "guide" modifiers).
   - Count total informational keywords found.
   - Assess entity strength based on:
     * Authority score relative to competitors
     * Backlink profile quality
     * Brand keyword presence in organic keywords
     * Entity signals from Phase 1 (business_analysis.json)

6. Save the result to /home/ubuntu/output/market_intelligence.json.
7. Print a summary of key findings to the console.
"""

# ── Save template ─────────────────────────────────────────────
OUTPUT_DIR = "/home/ubuntu/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# json.dump(market_intelligence, open(os.path.join(OUTPUT_DIR, "market_intelligence.json"), 'w'), indent=2)
