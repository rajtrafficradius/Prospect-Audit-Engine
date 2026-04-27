import os
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

async def scrape_page(page, url, retry_count=2):
    """Scrapes the visible text from a given URL with stealth and Cloudflare-bypass logic."""
    for attempt in range(retry_count + 1):
        try:
            # wait_until="load" is safer for complex sites than domcontentloaded
            await page.goto(url, wait_until="load", timeout=30000)
            
            # Anti-Bot / Cloudflare Challenge Wait
            print(f" [+] Waiting for {url} to settle (Anti-Bot Challenge)...")
            await page.wait_for_timeout(6000) # Give 6s for Cloudflare/WAF to bypass
            
            # Check for Cloudflare/Cookie gate text
            content_preview = await page.evaluate("() => document.body ? document.body.innerText.slice(0, 500) : ''")
            if "checking your browser" in content_preview.lower() or "enable cookies" in content_preview.lower():
                print(f" [!] Site blocked by security gate. Waiting longer...")
                await page.wait_for_timeout(5000)

            # Extract text safely
            content = await page.evaluate("() => document.body ? document.body.innerText : ''")
            if len(content.strip()) > 300:
                return {"url": url, "content": " ".join(content.split())}
                
            # Fallback for empty body/protected content
            print(f" [!] Shallow content for {url} ({len(content)} chars). Attempting raw HTML capture...")
            html_content = await page.content()
            return {"url": url, "content": html_content[:8000]} # Increase limit for raw HTML
            
        except Exception as e:
            if "context was destroyed" in str(e) and attempt < retry_count:
                print(f" [!] Context destroyed for {url}, retrying ({attempt+1}/{retry_count})...")
                await asyncio.sleep(2)
                continue
            print(f"Error scraping {url}: {e}")
            return {"url": url, "content": ""}
    return {"url": url, "content": ""}

async def scrape_website_core_pages(base_url, output_dir=None):
    """
    Crawls the homepage and attempts to find/scrape About, Services, and Contact pages.
    Also takes a full-page screenshot of the homepage for Vision CRO analysis.
    Returns a dictionary of scraped data with stealth headers.
    """
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"
        
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled" # Stealth
            ]
        )
        # Use realistic headers
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Scrape Homepage
        print(f"Scraping Homepage (Stealth Mode): {base_url}")
        
        # Take screenshot for Vision Agent
        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000) # Give it 4 seconds to render images
            screenshot_path = os.path.join(output_dir, "homepage_screenshot.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Saved UI Screenshot: {screenshot_path}")
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            
        home_data = await scrape_page(page, base_url)
        results.append(home_data)

        # Attempt to find links to key pages with a safety guard
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
            links = await page.evaluate('''() => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors.map(a => ({ 
                    text: (a.innerText || a.textContent || "").toLowerCase(), 
                    href: a.href 
                })).filter(l => l.href && l.href.startsWith('http'));
            }''')
            
            # Filter for common core pages
            core_paths = set()
            for link in links:
                text = link.get('text', '')
                href = link.get('href', '')
                if 'about' in text or 'contact' in text or 'service' in text:
                    if href.startswith('http') and urlparse(href).netloc == urlparse(base_url).netloc:
                         core_paths.add(href)
            
            # Scrape up to 4 additional core pages to keep LLM context size reasonable
            for url in list(core_paths)[:4]:
                print(f"Scraping subpage: {url}")
                page_data = await scrape_page(page, url)
                results.append(page_data)

        except Exception as e:
            print(f"Could not discover subpages: {e}")

        await browser.close()
        
    return results

def run_scraper(base_url, output_dir=None):
    """Synchronous wrapper for the async scraper."""
    return asyncio.run(scrape_website_core_pages(base_url, output_dir))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data = run_scraper(sys.argv[1])
        for p in data:
            print(f"--- {p['url']} ---")
            print(p['content'][:200] + "...\n")
