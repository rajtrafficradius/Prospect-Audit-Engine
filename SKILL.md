---
name: prospect-audit-strategy-seo-geo-aeo
description: "Productized SEO, GEO (Generative Engine Optimization), and AEO (Answer Engine Optimization) prospect audit and strategy for Traffikis/TrafficRadius. Use when a user provides a website URL and requests a lightweight, productized audit and strategy for client acquisition. Produces four deliverables: a branded DOCX strategy document, two branded Excel workbooks (keyword data and action plan), and a premium client-facing slide deck."
---

# Prospect Audit & Strategy (SEO + GEO + AEO)

## 1. Overview

This skill executes a productized, automated process for creating a high-impact prospect audit and strategy package that covers all three layers of modern search: **SEO, GEO, and AEO**. It takes a single website URL as input and generates four professional, TrafficRadius-branded deliverables designed for client acquisition. The process is intentionally lightweight and cost-effective, making it ideal for use as a sales tool.

### The Three Layers of Modern Search

1.  **SEO (Search Engine Optimization):** The traditional foundation. Optimizing for rankings in classic search engine results pages (SERPs).
2.  **AEO (Answer Engine Optimization):** Optimizing to *be the answer* in formats like Featured Snippets, People Also Ask (PAA), and voice search results.
3.  **GEO (Generative Engine Optimization):** Optimizing to be cited and recommended by AI-powered search platforms like ChatGPT, Google AI Overviews, Perplexity, and Copilot.

This skill audits and builds strategies for all three layers.

### Key Principles

These principles MUST be followed throughout the entire process:

1.  **Strategic Level Only:** All content must be at a strategic level (the *what* and *why*), NOT execution-level detail (the *how*).
2.  **Zero Projections:** There must be **ZERO** traffic, revenue, lead, or ranking projections or guarantees.
3.  **Data-Driven:** All claims and recommendations must be grounded in real SEMrush data.
4.  **Opportunity-Focused:** The tone must be positive and opportunity-focused.
5.  **TrafficRadius Branding:** All deliverables use TrafficRadius branding (navy/blue/white palette, logo, copyright footer).
6.  **Budget-Conscious:** SEMrush API usage must stay within the ~10,000–15,000 unit budget.

### Input & Output

| Item | Detail |
|---|---|
| **Input** | A single website URL (e.g., `https://example.com.au`) |
| **Output 1** | Branded DOCX — Full SEO, GEO & AEO audit & strategy document |
| **Output 2** | Branded XLSX — Keyword & opportunity data workbook |
| **Output 3** | Branded XLSX — 90-day integrated action plan workbook |
| **Output 4** | Premium Slide Deck — 16–20 slides covering the full SEO, GEO & AEO strategy |

---

## 2. The 7-Phase Integrated Workflow

Execute these phases **in strict order**.

1.  **Integrated Discovery & Business Intelligence (SEO+GEO+AEO)**
2.  **Multi-Layer Market & Competitive Intelligence**
3.  **Integrated SEO, GEO & AEO Audit**
4.  **Holistic Keyword & Opportunity Research**
5.  **Integrated SEO, GEO & AEO Strategy Formulation**
6.  **Branded Deliverable Generation**
7.  **Quality Assurance & Delivery**

---

### Phase 1: Integrated Discovery & Business Intelligence

**Objective:** Understand the prospect’s business, services, entities, and target market to inform the SEO, GEO, and AEO strategy.

**Process:**
1.  Browse the prospect’s website (Homepage, About, Services, Contact, Blog).
2.  Use the schema in `scripts/business_discovery.py` to extract and record:
    *   Core business info, services/products, industry, target audience.
    *   **Entity & Authority Signals:** Extract key people, brand names, and NAP (Name, Address, Phone) for entity consistency checks.
    *   **AEO/GEO Seed Content:** Identify existing FAQ sections, “how-to” guides, and other question-based content.
    *   **Seed Keywords:** Generate 10-20 seed keywords, including traditional service terms and question-based queries (e.g., “how much does steel fabrication cost”).
3.  Save all findings to `/home/ubuntu/output/business_analysis.json`.

**Output:** `business_analysis.json`

---

### Phase 2: Multi-Layer Market & Competitive Intelligence

**Objective:** Establish a baseline of the prospect’s performance and competitive position across SEO, AEO, and GEO.

**Budget:** ~6,000–9,000 SEMrush API units.

**Process:**
1.  Read `scripts/semrush_intelligence.py` for the updated output schema.
2.  Execute SEMrush MCP calls to gather:
    *   **SEO Data:** Domain ranks, organic keywords, top competitors, and backlink overview for the prospect and top 3-5 competitors.
    *   **AEO Data:** Use `semrush_phrase_questions` and `semrush_phrase_related` on top non-branded keywords to find Featured Snippet and PAA opportunities.
    *   **GEO Data:** While direct GEO metrics aren't in the API yet, use keyword data to identify informational queries that are likely to trigger AI-generated answers.
3.  Parse all outputs and save to `/home/ubuntu/output/market_intelligence.json`.

**Output:** `market_intelligence.json`

---

### Phase 3: Integrated SEO, GEO & AEO Audit

**Objective:** Perform a focused audit to find high-impact issues and opportunities across all three layers.

**Process:**
1.  Read the updated `references/audit_checklist.md` for the full SEO, GEO, and AEO checklist.
2.  Adapt and run `scripts/technical_cro_audit.py` to automatically check:
    *   **SEO:** `sitemap.xml`, on-page elements, site speed, mobile-friendliness.
    *   **GEO:** `robots.txt` for AI bot blocking (GPTBot, ClaudeBot, PerplexityBot, Google-Extended), and presence of `llms.txt`.
    *   **AEO/GEO:** Expanded schema checks (FAQPage, HowTo, Article, ProfilePage), content structure for AI (direct answers, lists, tables).
3.  **Additionally, the agent must manually assess**:
    *   Entity consistency and authority signals.
    *   Clarity of CTAs and lead capture forms.
4.  Save all findings to `/home/ubuntu/output/audit_findings.json`.

**Output:** `audit_findings.json`

---

### Phase 4: Holistic Keyword & Opportunity Research

**Objective:** Build a focused list of 150-250 opportunities, including traditional keywords, questions, and entity-related queries.

**Budget:** ~4,000–6,000 SEMrush API units.

**Process:**
1.  Read `scripts/keyword_research.py` for processing functions.
2.  Use seed keywords from Phase 1 to run `semrush_phrase_related` and `semrush_phrase_questions`.
3.  Process all raw keyword data, categorizing each opportunity by type:
    *   **SEO:** Commercial and transactional keywords.
    *   **AEO:** Question-based keywords (how, what, why, where).
    *   **GEO:** Long-tail informational and conversational queries.
4.  Calculate an updated Opportunity Score for each keyword.
5.  Save to `/home/ubuntu/output/keyword_opportunities.csv`.

**Output:** `keyword_opportunities.csv`

---

### Phase 5: Integrated SEO, GEO & AEO Strategy Formulation

**Objective:** Synthesize all data into a compelling, three-layer strategic narrative and a 90-day action plan.

**Process:**
1.  Read the updated `references/strategy_template.md` for the new structure.
2.  Load all data files from previous phases.
3.  Write the full strategy document, outlining the integrated three-pillar strategy:
    *   **Pillar 1: SEO Foundation:** Technical health, on-page optimization, and authority building.
    *   **Pillar 2: AEO & Answerability:** Content structured to win answer boxes and featured snippets.
    *   **Pillar 3: GEO & AI Visibility:** Optimizing for citations and recommendations in generative AI.
4.  Save to `/home/ubuntu/output/strategy_document.md`.

**Output:** `strategy_document.md`

---

### Phase 6: Branded Deliverable Generation

**Objective:** Programmatically create all four final, branded deliverables reflecting the integrated strategy.

**Process:**
1.  **Generate Charts:** Run the updated `scripts/create_charts.py` to generate new and updated visualizations, including a three-layer strategy diagram and an AEO/GEO readiness scorecard.
2.  **Generate DOCX:** Run the updated `scripts/create_strategy_docx.py` to build the full strategy document with the new sections and charts.
3.  **Generate Keyword XLSX:** Run the updated `scripts/create_keyword_xlsx.py` to populate the workbook with SEO, AEO, and GEO keyword opportunities.
4.  **Generate Action Plan XLSX:** Run the updated `scripts/create_action_plan_xlsx.py` with integrated SEO, AEO, and GEO tasks for each month.
5.  **Generate Slides:** Create `slide_content.md` based on the updated `references/slide_outline_template.md`, then use the `slides` tool to generate the deck.

**Outputs:** All four final deliverables.

---

### Phase 7: Quality Assurance & Delivery

**Objective:** Validate all deliverables against the updated quality checklist.

**Process:**
1.  Read the updated `references/quality_checklist.md`.
2.  Verify every item, paying special attention to the new GEO and AEO checks (e.g., `GEO-01: AI bot access checked`, `AEO-01: FAQ/Question opportunities identified`).
3.  Deliver all four validated deliverables to the user.

---

## 3. SEMrush Budget Summary (Updated)

| Phase | Calls | Estimated Units |
|---|---|---|
| Phase 2: Market Intelligence | 8–12 calls | 6,000–9,000 |
| Phase 4: Keyword Research | 10–15 calls | 4,000–6,000 |
| **Total** | **18–27 calls** | **10,000–15,000** |

This updated workflow provides a far more comprehensive and future-proof strategy while remaining budget-conscious.
