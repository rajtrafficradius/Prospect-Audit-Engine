#!/usr/bin/env python3
"""
Prospect Audit & Strategy — Phase 3: Integrated SEO, GEO & AEO Audit
=====================================================================
Automated technical checks across all three layers of modern search,
plus CRO assessment.

This script is a TEMPLATE. The agent adapts the PROSPECT_DOMAIN variable
and runs the script. Manual CRO/entity observations are added afterward.

Usage: python3 technical_cro_audit.py <domain>
       e.g., python3 technical_cro_audit.py example.com.au
"""

import json
import os
import sys
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/home/ubuntu/output")

# ══════════════════════════════════════════════════════════════
# OUTPUT SCHEMA
# ══════════════════════════════════════════════════════════════

audit_findings = {
    "seo_findings": [],
    "aeo_findings": [],
    "geo_findings": [],
    "cro_findings": [],   # Populated by agent after manual assessment
    "scorecard": {
        "seo_score": 0,
        "aeo_score": 0,
        "geo_score": 0,
        "cro_score": 50,  # Default baseline, adjusted by manual assessment
        "overall_score": 0,
    },
}

# Finding template:
# {
#     "layer": "SEO" | "AEO" | "GEO" | "CRO",
#     "severity": "Critical" | "High" | "Medium" | "Opportunity",
#     "area": "...",
#     "title": "...",
#     "description": "...",
#     "recommendation": "...",
#     "current_status": "PASS" | "FAIL" | "WARNING" | "Missing" | "Present",
# }


# ══════════════════════════════════════════════════════════════
# SEO CHECKS
# ══════════════════════════════════════════════════════════════

def check_robots_txt(base_url):
    """Check robots.txt for SEO blocking issues."""
    try:
        resp = requests.get(urljoin(base_url, '/robots.txt'), timeout=10)
        if resp.status_code == 200:
            content = resp.text
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.lower() == 'disallow: /':
                    return {
                        "layer": "SEO", "severity": "Critical", "area": "Indexability",
                        "title": "robots.txt blocks the entire site",
                        "description": "The robots.txt contains 'Disallow: /' which blocks all crawlers.",
                        "recommendation": "Remove or modify the Disallow directive.",
                        "current_status": "FAIL"
                    }
            return {
                "layer": "SEO", "severity": "Info", "area": "Indexability",
                "title": "robots.txt is properly configured",
                "description": "robots.txt exists and does not block critical pages.",
                "recommendation": "No action needed.",
                "current_status": "PASS"
            }
        elif resp.status_code == 404:
            return {
                "layer": "SEO", "severity": "Medium", "area": "Indexability",
                "title": "No robots.txt file found",
                "description": "The website does not have a robots.txt file.",
                "recommendation": "Create a robots.txt with appropriate directives and sitemap reference.",
                "current_status": "Missing"
            }
    except Exception as e:
        return {
            "layer": "SEO", "severity": "Medium", "area": "Indexability",
            "title": "Could not access robots.txt",
            "description": f"Error: {str(e)}",
            "recommendation": "Ensure the server is accessible.",
            "current_status": "ERROR"
        }


def check_sitemap(base_url):
    """Check for XML sitemap."""
    try:
        resp = requests.get(urljoin(base_url, '/sitemap.xml'), timeout=10)
        if resp.status_code == 200 and ('<?xml' in resp.text or '<urlset' in resp.text or '<sitemapindex' in resp.text):
            return {
                "layer": "SEO", "severity": "Info", "area": "Indexability",
                "title": "XML Sitemap found",
                "description": "sitemap.xml is present and appears valid.",
                "recommendation": "Ensure all important pages are included.",
                "current_status": "PASS"
            }
        else:
            return {
                "layer": "SEO", "severity": "High", "area": "Indexability",
                "title": "No XML Sitemap found",
                "description": "No sitemap.xml at the standard location.",
                "recommendation": "Create and submit an XML sitemap.",
                "current_status": "FAIL"
            }
    except Exception as e:
        return {
            "layer": "SEO", "severity": "High", "area": "Indexability",
            "title": "Could not access sitemap.xml",
            "description": f"Error: {str(e)}",
            "recommendation": "Create an XML sitemap.",
            "current_status": "ERROR"
        }


def check_homepage_seo(base_url):
    """Check on-page SEO elements of the homepage."""
    findings = []
    try:
        resp = requests.get(base_url, timeout=15, allow_redirects=True)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Title tag
        title = soup.find('title')
        if not title or not title.string:
            findings.append({
                "layer": "SEO", "severity": "Critical", "area": "On-Page SEO",
                "title": "Missing title tag on homepage",
                "description": "The homepage has no <title> tag.",
                "recommendation": "Add a descriptive, keyword-rich title (50-60 chars).",
                "current_status": "FAIL"
            })
        else:
            title_len = len(title.string.strip())
            if title_len < 30 or title_len > 65:
                findings.append({
                    "layer": "SEO", "severity": "Medium", "area": "On-Page SEO",
                    "title": f"Title tag length issue ({title_len} chars)",
                    "description": f"Current title: '{title.string.strip()[:60]}...' Optimal: 50-60 chars.",
                    "recommendation": "Optimize title tag length.",
                    "current_status": "WARNING"
                })

        # H1 tag
        h1_tags = soup.find_all('h1')
        if len(h1_tags) == 0:
            findings.append({
                "layer": "SEO", "severity": "High", "area": "On-Page SEO",
                "title": "Missing H1 tag on homepage",
                "description": "No H1 heading found.",
                "recommendation": "Add a single, descriptive H1 with the primary keyword.",
                "current_status": "FAIL"
            })
        elif len(h1_tags) > 1:
            findings.append({
                "layer": "SEO", "severity": "Medium", "area": "On-Page SEO",
                "title": f"Multiple H1 tags ({len(h1_tags)})",
                "description": f"Found {len(h1_tags)} H1 tags. Best practice is one.",
                "recommendation": "Consolidate to a single H1.",
                "current_status": "WARNING"
            })

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc or not meta_desc.get('content'):
            findings.append({
                "layer": "SEO", "severity": "High", "area": "On-Page SEO",
                "title": "Missing meta description",
                "description": "No meta description tag found.",
                "recommendation": "Add a compelling meta description (150-160 chars).",
                "current_status": "FAIL"
            })

    except Exception as e:
        findings.append({
            "layer": "SEO", "severity": "Critical", "area": "Accessibility",
            "title": "Could not access homepage",
            "description": f"Error: {str(e)}",
            "recommendation": "Ensure the website is accessible.",
            "current_status": "ERROR"
        })
    return findings


# ══════════════════════════════════════════════════════════════
# GEO CHECKS
# ══════════════════════════════════════════════════════════════

def check_ai_bot_access(base_url):
    """Check robots.txt for AI bot blocking (GEO)."""
    findings = []
    ai_bots = {
        "GPTBot": "gptbot",
        "ClaudeBot": "claudebot",
        "PerplexityBot": "perplexitybot",
        "Google-Extended": "google-extended",
    }
    try:
        resp = requests.get(urljoin(base_url, '/robots.txt'), timeout=10)
        if resp.status_code == 200:
            content = resp.text.lower()
            for display_name, bot_id in ai_bots.items():
                if bot_id in content:
                    # Check if blocked
                    lines = content.split('\n')
                    current_agent = ""
                    is_blocked = False
                    for line in lines:
                        line = line.strip()
                        if line.startswith("user-agent:"):
                            current_agent = line.split(":", 1)[1].strip()
                        elif line.startswith("disallow:") and current_agent == bot_id:
                            disallow_path = line.split(":", 1)[1].strip()
                            if disallow_path == "/" or disallow_path == "":
                                is_blocked = True
                    if is_blocked:
                        findings.append({
                            "layer": "GEO", "severity": "Critical", "area": "AI Bot Access",
                            "title": f"{display_name} is BLOCKED in robots.txt",
                            "description": f"{display_name} is explicitly blocked, preventing AI search engines from indexing content.",
                            "recommendation": f"Allow {display_name} access to public content pages.",
                            "current_status": "FAIL"
                        })
                    else:
                        findings.append({
                            "layer": "GEO", "severity": "Info", "area": "AI Bot Access",
                            "title": f"{display_name} is allowed",
                            "description": f"{display_name} is mentioned but not blocked.",
                            "recommendation": "No action needed.",
                            "current_status": "PASS"
                        })
                else:
                    findings.append({
                        "layer": "GEO", "severity": "Info", "area": "AI Bot Access",
                        "title": f"{display_name} not mentioned (allowed by default)",
                        "description": f"{display_name} is not mentioned in robots.txt, so it has default access.",
                        "recommendation": "No action needed.",
                        "current_status": "PASS"
                    })
    except:
        findings.append({
            "layer": "GEO", "severity": "Medium", "area": "AI Bot Access",
            "title": "Could not check AI bot access",
            "description": "robots.txt could not be accessed to verify AI bot permissions.",
            "recommendation": "Manually verify robots.txt.",
            "current_status": "ERROR"
        })
    return findings


def check_llms_txt(base_url):
    """Check for llms.txt presence (GEO best practice)."""
    try:
        domain = base_url.replace("https://", "").replace("http://", "").rstrip("/")
        resp = requests.get(f"https://{domain}/llms.txt", timeout=10, allow_redirects=True)
        if resp.status_code == 200 and len(resp.text.strip()) > 10:
            return {
                "layer": "GEO", "severity": "Info", "area": "AI Guidance",
                "title": "llms.txt file found",
                "description": "An llms.txt file exists, guiding AI systems on how to interpret the site.",
                "recommendation": "Ensure the file is up to date.",
                "current_status": "PASS"
            }
        else:
            return {
                "layer": "GEO", "severity": "Medium", "area": "AI Guidance",
                "title": "No llms.txt file found",
                "description": "No llms.txt file exists. This is an emerging best practice for guiding AI systems.",
                "recommendation": "Create an llms.txt file to help AI engines understand your site structure.",
                "current_status": "Missing"
            }
    except:
        return {
            "layer": "GEO", "severity": "Medium", "area": "AI Guidance",
            "title": "No llms.txt file found",
            "description": "No llms.txt file exists.",
            "recommendation": "Create an llms.txt file.",
            "current_status": "Missing"
        }


# ══════════════════════════════════════════════════════════════
# AEO + GEO SCHEMA CHECKS
# ══════════════════════════════════════════════════════════════

def check_schema_and_content_structure(base_url):
    """Check schema markup (AEO+GEO) and content structure for answers (AEO)."""
    aeo_findings = []
    geo_findings = []
    try:
        resp = requests.get(base_url, timeout=15, allow_redirects=True)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract all schema types
        schema_types = []
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if '@type' in item:
                            schema_types.append(item['@type'])
                elif isinstance(data, dict):
                    if '@type' in data:
                        schema_types.append(data['@type'])
                    if '@graph' in data:
                        for item in data['@graph']:
                            if '@type' in item:
                                schema_types.append(item['@type'])
            except:
                pass

        # AEO: FAQPage schema
        if "FAQPage" in schema_types:
            aeo_findings.append({
                "layer": "AEO", "severity": "Info", "area": "Schema for Answers",
                "title": "FAQPage schema found",
                "description": "FAQPage structured data is present, helping content appear in answer boxes.",
                "recommendation": "Ensure FAQs are on all relevant service pages.",
                "current_status": "PASS"
            })
        else:
            aeo_findings.append({
                "layer": "AEO", "severity": "High", "area": "Schema for Answers",
                "title": "No FAQPage schema found",
                "description": "No FAQPage structured data. This is critical for appearing in answer boxes and PAA.",
                "recommendation": "Implement FAQPage schema on pages with Q&A content.",
                "current_status": "FAIL"
            })

        # AEO: HowTo schema
        if "HowTo" in schema_types:
            aeo_findings.append({
                "layer": "AEO", "severity": "Info", "area": "Schema for Answers",
                "title": "HowTo schema found",
                "description": "HowTo structured data is present.",
                "recommendation": "Ensure HowTo schema is on all relevant guide pages.",
                "current_status": "PASS"
            })
        else:
            aeo_findings.append({
                "layer": "AEO", "severity": "Medium", "area": "Schema for Answers",
                "title": "No HowTo schema found",
                "description": "No HowTo structured data. This helps content appear in step-by-step answer formats.",
                "recommendation": "Implement HowTo schema on guide and tutorial pages.",
                "current_status": "Missing"
            })

        # GEO: Organization/LocalBusiness schema
        has_org = any(t in schema_types for t in ["Organization", "LocalBusiness"])
        if has_org:
            geo_findings.append({
                "layer": "GEO", "severity": "Info", "area": "Entity Authority",
                "title": "Organization schema found",
                "description": f"Schema types found: {', '.join(schema_types)}. This strengthens entity signals for AI engines.",
                "recommendation": "Ensure all attributes are complete (name, logo, address, social profiles).",
                "current_status": "PASS"
            })
        else:
            geo_findings.append({
                "layer": "GEO", "severity": "High", "area": "Entity Authority",
                "title": "No Organization/LocalBusiness schema found",
                "description": "Missing Organization schema weakens entity signals for AI engines.",
                "recommendation": "Implement Organization or LocalBusiness schema with complete attributes.",
                "current_status": "FAIL"
            })

        # GEO: Person/Author schema
        has_author = any(t in schema_types for t in ["Person", "ProfilePage"])
        if has_author:
            geo_findings.append({
                "layer": "GEO", "severity": "Info", "area": "Entity Authority",
                "title": "Author/Person schema found",
                "description": "Person schema strengthens author entity signals for AI citations.",
                "recommendation": "Ensure author bios are linked to published content.",
                "current_status": "PASS"
            })
        else:
            geo_findings.append({
                "layer": "GEO", "severity": "Medium", "area": "Entity Authority",
                "title": "No Author/Person schema found",
                "description": "Missing author schema. AI engines use author signals to assess content authority.",
                "recommendation": "Implement Person schema for key authors and experts.",
                "current_status": "Missing"
            })

        # AEO: Content structure for answers
        question_headings = 0
        for tag in soup.find_all(['h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if '?' in text:
                question_headings += 1

        has_lists = len(soup.find_all(['ul', 'ol'])) > 2
        has_tables = len(soup.find_all('table')) > 0
        page_text = soup.get_text().lower()
        has_faq_text = any(term in page_text for term in ['faq', 'frequently asked', 'common questions'])

        if question_headings > 0 and (has_lists or has_tables):
            aeo_findings.append({
                "layer": "AEO", "severity": "Info", "area": "Content Structure",
                "title": "Content is well-structured for answer engines",
                "description": f"Found {question_headings} question headings, structured lists, and/or tables.",
                "recommendation": "Expand Q&A content to more service pages.",
                "current_status": "PASS"
            })
        elif has_lists or has_tables:
            aeo_findings.append({
                "layer": "AEO", "severity": "Medium", "area": "Content Structure",
                "title": "Content partially structured for answers",
                "description": "Content uses lists/tables but lacks direct Q&A format headings.",
                "recommendation": "Add question-format headings (H2/H3) and direct answer paragraphs.",
                "current_status": "WARNING"
            })
        else:
            aeo_findings.append({
                "layer": "AEO", "severity": "High", "area": "Content Structure",
                "title": "Content not structured for answer engines",
                "description": "Content lacks structured elements (lists, tables, Q&A headings) needed for answer engines.",
                "recommendation": "Restructure content with question headings, lists, tables, and direct answers.",
                "current_status": "FAIL"
            })

    except Exception as e:
        aeo_findings.append({
            "layer": "AEO", "severity": "Medium", "area": "Schema",
            "title": "Could not check schema and content structure",
            "description": f"Error: {str(e)}",
            "recommendation": "Manually check schema markup.",
            "current_status": "ERROR"
        })

    return aeo_findings, geo_findings


# ══════════════════════════════════════════════════════════════
# SCORING
# ══════════════════════════════════════════════════════════════

def calculate_integrated_scores(seo_findings, aeo_findings, geo_findings):
    """Calculate scorecard scores for each layer (0-100)."""
    def score_layer(findings):
        if not findings:
            return 50
        total = len(findings)
        pass_count = sum(1 for f in findings if f.get("current_status") in ["PASS", "Info"])
        fail_count = sum(1 for f in findings if f.get("current_status") == "FAIL")
        critical_count = sum(1 for f in findings if f.get("severity") == "Critical" and f.get("current_status") == "FAIL")
        score = int((pass_count / max(total, 1)) * 100)
        score -= critical_count * 15
        score -= fail_count * 5
        return max(0, min(100, score))

    seo_score = score_layer(seo_findings)
    aeo_score = score_layer(aeo_findings)
    geo_score = score_layer(geo_findings)
    cro_score = 50  # Adjusted by manual assessment
    overall = int((seo_score + aeo_score + geo_score + cro_score) / 4)

    return {
        "seo_score": seo_score,
        "aeo_score": aeo_score,
        "geo_score": geo_score,
        "cro_score": cro_score,
        "overall_score": overall,
    }


# ══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 technical_cro_audit.py <domain>")
        print("Example: python3 technical_cro_audit.py example.com.au")
        sys.exit(1)

    domain = sys.argv[1].replace("https://", "").replace("http://", "").rstrip("/")
    base_url = f"https://{domain}"

    print(f"\n{'='*60}")
    print(f"  INTEGRATED SEO, GEO & AEO AUDIT: {domain}")
    print(f"{'='*60}\n")

    seo_findings = []
    aeo_findings = []
    geo_findings = []

    # SEO Checks
    print("[1/5] Checking robots.txt (SEO)...")
    result = check_robots_txt(base_url)
    if result:
        seo_findings.append(result)
        print(f"  → {result['current_status']}: {result['title']}")

    print("[2/5] Checking sitemap.xml (SEO)...")
    result = check_sitemap(base_url)
    if result:
        seo_findings.append(result)
        print(f"  → {result['current_status']}: {result['title']}")

    print("[3/5] Checking homepage on-page SEO...")
    homepage_results = check_homepage_seo(base_url)
    seo_findings.extend(homepage_results)
    for f in homepage_results:
        print(f"  → {f['current_status']}: {f['title']}")

    # GEO Checks
    print("[4/5] Checking AI bot access & llms.txt (GEO)...")
    ai_bot_results = check_ai_bot_access(base_url)
    geo_findings.extend(ai_bot_results)
    blocked_count = sum(1 for f in ai_bot_results if f.get("current_status") == "FAIL")
    print(f"  → {blocked_count} AI bots blocked out of 4 checked")

    llms_result = check_llms_txt(base_url)
    geo_findings.append(llms_result)
    print(f"  → llms.txt: {llms_result['current_status']}")

    # AEO + GEO Schema Checks
    print("[5/5] Checking schema markup & content structure (AEO + GEO)...")
    aeo_schema_results, geo_schema_results = check_schema_and_content_structure(base_url)
    aeo_findings.extend(aeo_schema_results)
    geo_findings.extend(geo_schema_results)
    for f in aeo_schema_results:
        print(f"  → AEO {f['current_status']}: {f['title']}")
    for f in geo_schema_results:
        print(f"  → GEO {f['current_status']}: {f['title']}")

    # Calculate scores
    scores = calculate_integrated_scores(seo_findings, aeo_findings, geo_findings)

    # Populate output
    audit_findings["seo_findings"] = seo_findings
    audit_findings["aeo_findings"] = aeo_findings
    audit_findings["geo_findings"] = geo_findings
    audit_findings["scorecard"] = scores

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "audit_findings.json")
    with open(output_path, 'w') as f:
        json.dump(audit_findings, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  INTEGRATED AUDIT SCORECARD")
    print(f"{'='*60}")
    print(f"  SEO Score:     {scores['seo_score']}/100")
    print(f"  AEO Score:     {scores['aeo_score']}/100")
    print(f"  GEO Score:     {scores['geo_score']}/100")
    print(f"  CRO Score:     {scores['cro_score']}/100 (pending manual assessment)")
    print(f"  Overall Score: {scores['overall_score']}/100")
    print(f"{'='*60}")
    print(f"\nResults saved to: {output_path}")
    print("\nNOTE: The agent must also perform MANUAL assessment of:")
    print("  - CRO: CTA clarity, form usability, trust signals, navigation")
    print("  - GEO: Entity consistency, content freshness, author bios")
    print("  - AEO: Content quality on key service pages (beyond homepage)")
    print("  Update audit_findings.json with these manual observations.")
