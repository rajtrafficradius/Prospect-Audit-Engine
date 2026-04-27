#!/usr/bin/env python3
"""
Prospect Audit & Strategy — Phase 4: Multi-Layer Keyword Research (SEO + AEO + GEO)
====================================================================================
Uses SEMrush MCP to find 150-250 high-opportunity keywords, categorized
by search layer (SEO, AEO, GEO) and service cluster.

This script is a TEMPLATE/GUIDE. The agent executes SEMrush MCP calls
directly via manus-mcp-cli and processes the results using these functions.

BUDGET: ~3,000-5,000 SEMrush API units for keyword research.
"""

import json
import csv
import os
import re
import pandas as pd

# ══════════════════════════════════════════════════════════════
# CONFIGURATION — Update for each prospect
# ══════════════════════════════════════════════════════════════

PROSPECT_NAME = "{{PROSPECT_NAME}}"
PROSPECT_DOMAIN = "{{PROSPECT_DOMAIN}}"
OUTPUT_DIR = "/home/ubuntu/output"
DATABASE = "au"  # Default to Australia; change as needed

# ══════════════════════════════════════════════════════════════
# SEMRUSH MCP CALL SEQUENCE FOR MULTI-LAYER KEYWORD RESEARCH
# ══════════════════════════════════════════════════════════════

"""
The agent should use the CATEGORIZED seed keywords from business_analysis.json
and execute the following calls:

STEP 1: Load seed keywords from business_analysis.json
─────────────────────────────────────────────────────
with open(f"{OUTPUT_DIR}/business_analysis.json") as f:
    business = json.load(f)
seo_seeds = business["seed_keywords"]["seo_seeds"]
aeo_seeds = business["seed_keywords"]["aeo_seeds"]
geo_seeds = business["seed_keywords"]["geo_seeds"]

STEP 2: For each SEO seed keyword (top 5-8), get related keywords
──────────────────────────────────────────────────────────────
manus-mcp-cli tool call semrush_phrase_related --server semrush-mcp-v2 --input '{
    "phrase": "{{SEO_SEED}}",
    "database": "au",
    "display_limit": 50
}'

STEP 3: For each AEO seed keyword (top 3-5), get question keywords
────────────────────────────────────────────────────────────────
manus-mcp-cli tool call semrush_phrase_questions --server semrush-mcp-v2 --input '{
    "phrase": "{{AEO_SEED}}",
    "database": "au",
    "display_limit": 30
}'

STEP 4: For each GEO seed keyword (top 3-5), get related keywords
──────────────────────────────────────────────────────────────
manus-mcp-cli tool call semrush_phrase_related --server semrush-mcp-v2 --input '{
    "phrase": "{{GEO_SEED}}",
    "database": "au",
    "display_limit": 30
}'

STEP 5: Get keyword metrics for any additional terms
───────────────────────────────────────────────────
manus-mcp-cli tool call semrush_phrase_these --server semrush-mcp-v2 --input '{
    "phrase": "keyword1;keyword2;keyword3",
    "database": "au"
}'

ESTIMATED BUDGET: 3,000 - 5,000 units
"""

# ══════════════════════════════════════════════════════════════
# DATA PROCESSING FUNCTIONS
# ══════════════════════════════════════════════════════════════

def parse_semrush_output(raw_output):
    """
    Parse semicolon-delimited SEMrush output into a list of dicts.
    SEMrush returns data in format: header1;header2;...\nval1;val2;...
    """
    rows = []
    lines = raw_output.strip().split('\n')
    if len(lines) < 2:
        return rows

    headers = lines[0].split(';')
    for line in lines[1:]:
        if not line.strip() or 'ERROR' in line or 'NOTHING FOUND' in line:
            continue
        parts = line.split(';')
        if len(parts) >= len(headers):
            row = {}
            for i, h in enumerate(headers):
                row[h.strip()] = parts[i].strip()
            rows.append(row)
    return rows


def classify_search_layer(keyword):
    """
    Classify a keyword into its primary search layer: SEO, AEO, or GEO.

    - AEO: Question keywords (how, what, why, where, when, which, can, does, is)
           and direct-answer queries.
    - GEO: Informational/conversational queries that AI engines typically answer
           (best, vs, guide, review, comparison, pros and cons, explained).
    - SEO: Commercial/transactional keywords (everything else).
    """
    kw_lower = keyword.lower().strip()

    # AEO patterns: Question-based queries
    aeo_patterns = [
        r'^(how|what|why|where|when|which|who|can|does|is|are|do|should|will|would)\b',
        r'\?$',
    ]
    for pattern in aeo_patterns:
        if re.search(pattern, kw_lower):
            return "AEO"

    # GEO patterns: Informational/conversational queries AI engines answer
    geo_indicators = [
        'best ', ' best', ' vs ', ' versus ', ' compared to ', ' comparison',
        ' guide', ' explained', ' overview', ' pros and cons', ' review',
        ' alternatives', ' meaning', ' definition', ' types of ',
    ]
    for indicator in geo_indicators:
        if indicator in kw_lower:
            return "GEO"

    # Default: SEO (commercial/transactional)
    return "SEO"


def calculate_opportunity_score(volume, competition, cpc):
    """
    Opportunity Score = Volume * (1 - Competition) * (1 + CPC)
    Higher score = higher volume, lower competition, higher commercial value.
    """
    try:
        vol = float(volume)
        comp = float(competition)
        cost = float(cpc)
        return round(vol * (1 - comp) * (1 + cost), 0)
    except (ValueError, TypeError):
        return 0


def categorize_keyword(keyword, service_categories):
    """
    Assign a keyword to a service/product category based on keyword matching.
    service_categories: dict of {category_name: [list of matching terms]}
    """
    kw_lower = keyword.lower()
    for category, terms in service_categories.items():
        if any(term.lower() in kw_lower for term in terms):
            return category
    return "General / Informational"


def process_keyword_data(all_raw_keywords, service_categories):
    """
    Process raw keyword data into a structured, scored, clustered, and
    layer-classified DataFrame.

    all_raw_keywords: list of dicts with keys like 'Keyword', 'Search Volume', 'CPC', 'Competition'
    """
    processed = []
    seen = set()

    for kw in all_raw_keywords:
        keyword = kw.get('Keyword', kw.get('keyword', kw.get('Phrase', ''))).strip()
        if not keyword or keyword.lower() in seen:
            continue
        seen.add(keyword.lower())

        volume = int(kw.get('Search Volume', kw.get('volume', kw.get('Volume', 0))) or 0)
        cpc = float(kw.get('CPC', kw.get('cpc', 0)) or 0)
        competition = float(kw.get('Competition', kw.get('competition', kw.get('Keyword Difficulty', 0))) or 0)

        if volume <= 0:
            continue

        # Normalize competition to 0-1 range if it's on 0-100 scale
        if competition > 1:
            competition = competition / 100.0

        cluster = categorize_keyword(keyword, service_categories)
        layer = classify_search_layer(keyword)
        score = calculate_opportunity_score(volume, competition, cpc)

        processed.append({
            'Keyword': keyword,
            'Search_Layer': layer,       # NEW: SEO, AEO, or GEO
            'Cluster': cluster,
            'Volume': volume,
            'CPC': round(cpc, 2),
            'Competition': round(competition, 2),
            'Opportunity_Score': score,
        })

    df = pd.DataFrame(processed)
    if len(df) > 0:
        df = df.sort_values('Opportunity_Score', ascending=False)
    return df


def generate_cluster_summary(df):
    """Generate a summary table grouped by keyword cluster."""
    if len(df) == 0:
        return pd.DataFrame()

    summary = df.groupby('Cluster').agg(
        Keywords=('Keyword', 'count'),
        Total_Volume=('Volume', 'sum'),
        Avg_CPC=('CPC', 'mean'),
        Avg_Competition=('Competition', 'mean'),
        Max_Volume=('Volume', 'max'),
    ).sort_values('Total_Volume', ascending=False)

    summary['Traffic_Value'] = (summary['Total_Volume'] * summary['Avg_CPC']).round(0)
    summary['Avg_CPC'] = summary['Avg_CPC'].round(2)
    summary['Avg_Competition'] = summary['Avg_Competition'].round(2)

    return summary


def generate_layer_summary(df):
    """Generate a summary table grouped by search layer (SEO, AEO, GEO)."""
    if len(df) == 0:
        return pd.DataFrame()

    summary = df.groupby('Search_Layer').agg(
        Keywords=('Keyword', 'count'),
        Total_Volume=('Volume', 'sum'),
        Avg_CPC=('CPC', 'mean'),
        Avg_Competition=('Competition', 'mean'),
        Top_Keyword=('Keyword', 'first'),
    ).sort_values('Total_Volume', ascending=False)

    summary['Avg_CPC'] = summary['Avg_CPC'].round(2)
    summary['Avg_Competition'] = summary['Avg_Competition'].round(2)

    return summary


# ══════════════════════════════════════════════════════════════
# MAIN EXECUTION TEMPLATE
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # The agent should:
    # 1. Load business_analysis.json to get categorized seed keywords and service categories
    # 2. Execute SEMrush MCP calls for each seed keyword (SEO, AEO, GEO seeds)
    # 3. Collect all raw keyword data
    # 4. Define service_categories dict based on the business analysis
    # 5. Call process_keyword_data() — this auto-classifies each keyword by layer
    # 6. Call generate_cluster_summary() and generate_layer_summary()
    # 7. Save results

    # Example service_categories (agent should build this from business_analysis.json):
    # service_categories = {
    #     "Steel Fabrication": ["steel fabricat", "metal fabricat", "welding", "cnc"],
    #     "Earthmoving": ["earthmoving", "excavator", "dozer"],
    #     ...
    # }

    # After processing:
    # df = process_keyword_data(all_raw_keywords, service_categories)
    # cluster_summary = generate_cluster_summary(df)
    # layer_summary = generate_layer_summary(df)

    # Save outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # df.to_csv(os.path.join(OUTPUT_DIR, "keyword_opportunities.csv"), index=False)
    # cluster_summary.to_csv(os.path.join(OUTPUT_DIR, "cluster_summary.csv"))
    # layer_summary.to_csv(os.path.join(OUTPUT_DIR, "layer_summary.csv"))

    # Print summary
    # print(f"Total keywords: {len(df)}")
    # print(f"Total search demand: {df['Volume'].sum():,}/mo")
    # print(f"\nBy Search Layer:")
    # print(layer_summary.to_string())
    # print(f"\nBy Service Cluster:")
    # print(cluster_summary.to_string())
    # print(f"\nTop 15 Opportunities:\n{df.head(15).to_string(index=False)}")

    print("Multi-layer keyword research template ready.")
    print("Agent should execute SEMrush calls and process data using the functions above.")
