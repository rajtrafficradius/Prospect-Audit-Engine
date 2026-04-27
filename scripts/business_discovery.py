#!/usr/bin/env python3
"""
Prospect Audit & Strategy — Phase 1: Integrated Business Discovery (SEO + GEO + AEO)
=====================================================================================
Crawls the prospect's website and extracts core business intelligence,
including entity signals (GEO) and answer-readiness indicators (AEO).

This script is a TEMPLATE. The agent performs the actual browsing and
populates the schema below, then saves it to business_analysis.json.
"""

import json
import os

# ══════════════════════════════════════════════════════════════
# OUTPUT SCHEMA — The agent must populate this structure
# ══════════════════════════════════════════════════════════════

business_analysis = {
    # ── Core Business Info ─────────────────────────────────
    "company_name": "",
    "domain": "",
    "tagline": "",
    "description": "",

    # ── Business Classification ────────────────────────────
    "business_type": "",          # "E-commerce" | "Services" | "Hybrid" | "SaaS" | "Other"
    "industry": "",
    "sub_industry": "",

    # ── Target Market ──────────────────────────────────────
    "target_audience": "",
    "geographic_focus": "",
    "market_position": "",

    # ── Services / Products ────────────────────────────────
    "primary_services": [],
    "secondary_services": [],
    "service_areas": [],

    # ── Digital Presence Assessment ────────────────────────
    "pages_crawled": [],
    "has_blog": False,
    "blog_frequency": "",         # "Weekly", "Monthly", "Inactive", "None"
    "has_testimonials": False,
    "has_case_studies": False,
    "has_contact_form": False,
    "cta_text": "",
    "social_profiles": [],

    # ── Technical Quick Check ──────────────────────────────
    "cms_detected": "",
    "ssl_enabled": True,
    "mobile_responsive": True,

    # ── Entity & Authority Signals (GEO) ───────────────────
    "entity_signals": {
        "key_people": [],             # Named individuals (founders, directors, experts)
        "brand_name_variations": [],  # All variations of the brand name found
        "nap_data": {                 # Name, Address, Phone for entity consistency
            "name": "",
            "address": "",
            "phone": "",
            "email": ""
        },
        "has_about_page": False,
        "has_author_bios": False,     # Blog posts have named author bios
        "has_wikipedia_presence": False,
        "industry_associations": [],  # Professional associations, certifications
    },

    # ── AEO/GEO Content Assessment ────────────────────────
    "aeo_geo_content": {
        "has_faq_sections": False,
        "faq_page_urls": [],
        "has_how_to_guides": False,
        "has_glossary": False,
        "content_uses_lists_tables": False,
        "content_answers_questions": False,
        "has_schema_markup_visible": False,
        "schema_types_found": [],     # e.g., ["Organization", "LocalBusiness", "FAQPage"]
    },

    # ── AI Bot Access (GEO) ────────────────────────────────
    "ai_bot_access": {
        "robots_txt_exists": False,
        "gptbot_blocked": False,
        "claudebot_blocked": False,
        "perplexitybot_blocked": False,
        "google_extended_blocked": False,
        "llms_txt_exists": False,
    },

    # ── Seed Keywords (Categorized by Layer) ───────────────
    "seed_keywords": {
        "seo_seeds": [],      # 8-12 commercial/transactional keywords
                              # e.g., ["steel fabrication sydney", "custom welding services"]
        "aeo_seeds": [],      # 3-5 question-based keywords
                              # e.g., ["how much does steel fabrication cost", "what is cnc cutting"]
        "geo_seeds": [],      # 3-5 informational/conversational keywords
                              # e.g., ["best steel fabricators in sydney", "steel vs aluminium fabrication"]
    },

    # ── Competitive Signals ────────────────────────────────
    "mentioned_competitors": [],
    "unique_selling_points": [],
}

# ══════════════════════════════════════════════════════════════
# INSTRUCTIONS FOR THE AGENT
# ══════════════════════════════════════════════════════════════

"""
STEP-BY-STEP PROCESS:

1. BROWSE HOMEPAGE:
   - Extract company name, tagline, description.
   - Identify primary CTA and its text.
   - Note the main navigation structure.
   - Check for trust signals (testimonials, logos, certifications).
   - Detect CMS from HTML source (look for wp-content, Shopify, etc.).
   - Check the footer for NAP data (Name, Address, Phone).
   - Identify social media profile links.

2. BROWSE ABOUT PAGE:
   - Extract key people names and titles (for GEO entity signals).
   - Look for brand story, history, and mission.
   - Note any industry associations or certifications.

3. BROWSE SERVICES/PRODUCTS PAGES:
   - List all primary and secondary services/products.
   - Extract the exact headings used (these become SEO seed keywords).
   - Note if content uses lists, tables, or structured formats (AEO readiness).
   - Look for FAQ sections on service pages.

4. BROWSE BLOG (if present):
   - Assess posting frequency.
   - Check if posts have named author bios (GEO entity signal).
   - Look for FAQ sections, how-to guides, or glossary content (AEO readiness).

5. BROWSE CONTACT PAGE:
   - Verify NAP data consistency.
   - Assess the contact form (number of fields, ease of use).

6. CHECK robots.txt (domain.com/robots.txt):
   - Look for blocks on GPTBot, ClaudeBot, PerplexityBot, Google-Extended.
   - Note any unusual Disallow rules.
   - Populate the ai_bot_access section.

7. CHECK llms.txt (domain.com/llms.txt):
   - Note if this file exists (GEO best practice).

8. CHECK FOR SCHEMA MARKUP (via browser console):
   - Run: document.querySelectorAll('script[type="application/ld+json"]')
   - Note which schema types are present (Organization, LocalBusiness, FAQPage, etc.).

9. GENERATE SEED KEYWORDS (Categorized):
   - SEO seeds: Service page headings + location modifiers (8-12 keywords).
   - AEO seeds: Question-based versions of top services (3-5 keywords).
     e.g., "how much does [service] cost", "what is [service]"
   - GEO seeds: Informational/conversational versions (3-5 keywords).
     e.g., "best [service] in [location]", "[service A] vs [service B]"

10. SAVE OUTPUT:
    - Populate the business_analysis dict above.
    - Save to /home/ubuntu/output/business_analysis.json.
"""

# ── Save helper ───────────────────────────────────────────────
OUTPUT_DIR = "/home/ubuntu/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, "business_analysis.json")

# The agent will populate this with real data and save it
# json.dump(business_analysis, open(output_path, 'w'), indent=2)
# print(f"Business analysis saved to: {output_path}")
