import os
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI

# ---------------------------------------------------------
# Define the Pydantic Schema that mirrors business_analysis.json
# ---------------------------------------------------------

class NAPData(BaseModel):
    name: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""

class EntitySignals(BaseModel):
    key_people: List[str] = Field(default_factory=list, description="Named individuals like founders/directors.")
    brand_name_variations: List[str] = Field(default_factory=list, description="Common names/spellings of the prospect to filter out branded keywords.")
    nap_data: NAPData = Field(default_factory=NAPData)
    has_about_page: bool = False
    industry_associations: List[str] = Field(default_factory=list)
    competitor_blacklist_terms: List[str] = Field(default_factory=list, description="Terms to AVOID in competitor analysis, e.g. 'countdown', 'blog', 'news', 'forum'.")

class AeoGeoContent(BaseModel):
    has_faq_sections: bool = False
    has_how_to_guides: bool = False
    content_uses_lists_tables: bool = False
    content_answers_questions: bool = False

class SeedKeywords(BaseModel):
    seo_seeds: List[str] = Field(description="8-12 STRICTLY commercial/transactional keywords only. NO brand names. NO informational 'how-to' queries. Focus on high-intent product/service terms.")
    aeo_seeds: List[str] = Field(description="3-5 question-based keywords e.g. 'how much does X cost'")
    geo_seeds: List[str] = Field(description="3-5 informational/conversational keywords e.g. 'best X in Y'")

class BusinessAnalysis(BaseModel):
    company_name: str
    domain: str
    tagline: str
    description: str
    business_type: str = Field(description="'E-commerce', 'Services', 'Hybrid', 'SaaS', or 'Other'")
    industry: str
    target_audience: str
    geographic_focus: str
    primary_services: List[str] = Field(description="List of primary services or products offered.")
    money_pages: List[str] = Field(description="URLs of the most important commercial/transactional pages (Products, Services, Categories).")
    has_testimonials: bool = False
    has_contact_form: bool = False
    cta_text: str = Field(description="The primary Call-To-Action text found on the site.")
    entity_signals: EntitySignals
    aeo_geo_content: AeoGeoContent
    seed_keywords: SeedKeywords
    unique_selling_points: List[str] = Field(default_factory=list)
    commercial_intent_focus: str = Field(description="A brief description of the core revenue-generating purpose of the site to guide competitor research.")
    negative_exclusion_criteria: List[str] = Field(default_factory=list, description="Specific topics, page types, or intents that are NOT relevant to the core business (e.g., 'Holiday Countdowns', 'Generic Wiki content', 'Informational blogs about X').")

# ---------------------------------------------------------
# Extraction Logic
# ---------------------------------------------------------

def extract_business_info(scraped_pages: List[dict], openai_api_key: Optional[str] = None) -> dict:
    """
    Takes a list of scraped page dictionaries [{"url": url, "content": text}]
    and uses OpenAI (GPT-4o) to extract structured business analysis.
    """
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    # Compile content
    combined_content = ""
    for page in scraped_pages:
        combined_content += f"\n\n--- PAGE: {page['url']} ---\n"
        combined_content += page['content'][:15000] # truncate to avoid excessive tokens if pages are huge

    system_prompt = (
        "You are an expert SEO/GEO/AEO strategist performing a business discovery phase for a new prospect.\n"
        "Carefully analyze the provided website content scraped from the prospect's website.\n"
        "Your GOAL is to identify the 'Commercial Core'—what they actually SELL.\n"
        "IGNORE informational blogs, internal news, or incidental seasonal content (like countdowns) unless they are the primary product.\n"
        "In 'negative_exclusion_criteria', list specific themes that should be stripped from the audit (e.g. if a furniture store has a christmas countdown, list 'Holiday/Seasonal Countdowns').\n"
        "Extract the required business intelligence and fill out the structured schema accurately.\n"
        "In 'seo_seeds', provide ONLY high-intent commercial keywords. ABSOLUTELY NO BRANDED TERMS.\n"
        "In 'competitor_blacklist_terms', identify terms that would indicate a non-commercial competitor (e.g., 'wiki', 'blog', 'news', 'countdown')."
    )

    print("Sending content to OpenAI for structured JSON extraction...")
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"WEBSITE CONTENT:\n{combined_content}"}
        ],
        response_format=BusinessAnalysis,
        temperature=0.1
    )

    structured_data = completion.choices[0].message.parsed.model_dump()
    return structured_data

if __name__ == "__main__":
    # Test script with dummy data if run directly
    dummy_data = [{"url": "https://example.com", "content": "Example Corp. We provide the best plumbing services in Sydney. Call us at 555-1234. FAQ: How much does plumbing cost? It varies."}]
    try:
        res = extract_business_info(dummy_data)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Extraction failed: {e}")
