import os
import base64
import json
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

class CroFinding(BaseModel):
    area: str = Field(description="The UI/UX element being critiqued (e.g., 'Primary CTA', 'Trust Signals', 'Lead Capture Form', 'Above-the-Fold Value Proposition').")
    current_status: str = Field(description="A brutally honest assessment of what is visually wrong or under-optimized on their current homepage.")
    opportunity: str = Field(description="The specific, conversion-optimized redesign recommendation.")

class CroAssessment(BaseModel):
    findings: List[CroFinding] = Field(description="Exactly 4 specific CRO findings extracted from the visual appraisal.")

def analyze_homepage_ui(image_path: str) -> dict:
    """
    Passes the full-page screenshot of the prospect to GPT-4o-Vision.
    Returns a structured assessment of conversion rate optimization gaps.
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Screenshot not found at {image_path}. Ensure the scraper successfully captured the UI.")
        
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
    prompt = """
    You are an elite, brutally honest Conversion Rate Optimization (CRO) and UI/UX expert at an enterprise marketing agency.
    Review the attached full-page screenshot of our prospect's homepage.
    
    Your task is to identify 4 critical conversion roadblocks or visually unappealing UX elements that are causing them to lose leads.
    Focus on heavily impactful areas:
    - Primary Call-To-Action (CTA) placement, color contrast, and phrasing.
    - Above-the-fold value proposition clarity.
    - Lack of visible Trust Signals (reviews, badges, phone numbers).
    - Form/Lead Capture friction.
    
    Do not be polite. Be objective, harsh, and professional. Describe exactly what you see in their terrible design, and prescribe the specific best-practice element we will build to fix it.
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        response_format=CroAssessment,
        temperature=0.1
    )
    
    return completion.choices[0].message.parsed.model_dump()

if __name__ == "__main__":
    # Local dry-run testing
    test_img = os.path.join(os.path.dirname(__file__), "..", "output", "homepage_screenshot.png")
    try:
        results = analyze_homepage_ui(test_img)
        print(json.dumps(results, indent=2))
        
        out_path = os.path.join(os.path.dirname(__file__), "..", "output", "cro_assessment.json")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved CRO findings to {out_path}")
    except Exception as e:
        print(f"Vision Agent failed: {e}")
