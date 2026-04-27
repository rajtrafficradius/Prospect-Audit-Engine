# Integrated SEO, AEO & GEO Audit Checklist

This checklist guides the automated audit script (`scripts/technical_cro_audit.py`). It is focused on high-impact items that can be checked quickly and programmatically across all three layers of modern search.

---

## SEO Checklist (Traditional)

| Severity | Area | Item to Check | Method |
|---|---|---|---|
| Critical | Indexability | `robots.txt` for `Disallow: /` or major directory blocks. | Direct file read |
| Critical | Indexability | Presence and validity of `/sitemap.xml`. | Direct file read & basic XML parse |
| Important | On-Page SEO | Missing or duplicate `<title>` tags on Homepage and key service pages. | HTML parse |
| Important | On-Page SEO | Missing or multiple `<h1>` tags on Homepage and key service pages. | HTML parse |
| Important | Site Speed | Core Web Vitals (LCP, FID, CLS) assessment. | Google PageSpeed Insights API call |
| Opportunity | HTTPS | Check for mixed content warnings (http:// resources on an https:// page). | HTML parse for `src="http://` |

---

## AEO Checklist (Answer Engine Optimization)

| Severity | Area | Item to Check | Method |
|---|---|---|---|
| High | Schema for Answers | Presence and validity of `FAQPage` schema on pages with Q&A content. | JSON-LD script tag search |
| High | Content for Answers | Use of clear question/answer formats, lists, and tables in the HTML. | HTML parse for `<h2>`, `<h3>` tags with question marks, `<ul>`, `<ol>`, `<table>` tags. |
| Medium | Schema for Answers | Presence of `HowTo` schema on guide/tutorial pages. | JSON-LD script tag search |
| Opportunity | Voice Readiness | Content uses a conversational tone and provides direct answers to common questions. | Qualitative assessment (future enhancement for script). |

---

## GEO Checklist (Generative Engine Optimization)

| Severity | Area | Item to Check | Method |
|---|---|---|---|
| Critical | AI Bot Accessibility | `robots.txt` for blocking `GPTBot`, `ClaudeBot`, `PerplexityBot`, or `Google-Extended`. | Direct file read |
| High | Entity Authority | Presence of `Organization` or `Person` schema with detailed attributes. | JSON-LD script tag search |
| Medium | AI Guidance | Presence of an `llms.txt` file in the root directory. | Direct file read |
| Medium | Content for Citations | Content freshness (e.g., "last updated" dates) and use of original data/research signals. | HTML parse for date strings. |
| Opportunity | Entity Consistency | Consistency of Name, Address, Phone (NAP) data across the site. | Heuristic analysis of footer/contact page. |

---

## CRO Checklist (Conversion Rate Optimization)

This remains a qualitative assessment, but its findings inform the overall user journey across all search layers.

| Severity | Area | Item to Assess | Method |
|---|---|---|---|
| High | Call-to-Action (CTA) | Clarity, visibility, and compelling nature of the primary CTA on the Homepage. | Heuristic analysis of button text, placement, and color contrast. |
| High | Lead Capture | Ease of use of the primary contact/quote form. | Heuristic analysis of form length and layout. |
| Medium | Trust Signals | Presence of testimonials, case studies, client logos, or certifications. | Search for keywords like "testimonial", "case study", "our clients". |
