import os
import re
import json
import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup
import faiss
import numpy as np
import tiktoken
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)

class DeepCrawlerRAG:
    """
    Crawls up to 100 pages from a domain's sitemap, chunks the text,
    embeds it via OpenAI, and stores it in a local FAISS vector database
    for rich RAG querying during strategy synthesis.
    """
    def __init__(self, domain: str, output_dir: str, max_pages: int = 100):
        self.domain = domain.replace("https://", "").replace("http://", "").strip("/")
        self.base_url = f"https://{self.domain}"
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.max_pages = max_pages
        
        self.client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.sync_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.enc = tiktoken.get_encoding("cl100k_base")
        
        self.faiss_index_path = os.path.join(self.output_dir, "vector_store.index")
        self.chunks_data_path = os.path.join(self.output_dir, "vector_chunks.json")

    async def _fetch_sitemap_urls(self):
        """Attempts to find the sitemap via robots.txt or sitemap.xml directly."""
        urls = set()
        async with aiohttp.ClientSession() as session:
            # Check robots.txt
            robots_url = f"{self.base_url}/robots.txt"
            try:
                async with session.get(robots_url, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        for line in text.split('\n'):
                            if line.lower().startswith('sitemap:'):
                                sitemap_url = line.split(':', 1)[1].strip()
                                urls.update(await self._parse_sitemap(session, sitemap_url))
            except Exception:
                pass

            # If no sitemap found in robots.txt, try standard locations
            if not urls:
                for path in ["/sitemap.xml", "/sitemap_index.xml"]:
                    urls.update(await self._parse_sitemap(session, f"{self.base_url}{path}"))
                    if urls: break
                    
        # Fallback to just the homepage if nothing is found
        if not urls:
            urls.add(self.base_url)
            
        return list(urls)[:self.max_pages]

    async def _parse_sitemap(self, session, sitemap_url):
        urls = set()
        try:
            async with session.get(sitemap_url, timeout=10) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    soup = BeautifulSoup(text, 'xml')
                    locs = soup.find_all('loc')
                    for loc in locs:
                        if loc.text:
                            url_text = loc.text.split('?')[0]
                            if url_text.endswith('.xml'):
                                if len(urls) < self.max_pages:
                                    # Nested sitemap (e.g. Shopify), recurse carefully
                                    urls.update(await self._parse_sitemap(session, loc.text))
                            else:
                                urls.add(loc.text)
                                if len(urls) >= self.max_pages:
                                    break
        except Exception:
            pass
        return urls

    async def _fetch_page(self, browser_context, url):
        """Fetches page content via Stealth Playwright with robust Cloudflare bypass."""
        page = await browser_context.new_page()
        try:
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Initial navigation
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                if "navigation" in str(e).lower():
                    # Likely a redirect or challenge page loading, wait and continue
                    await page.wait_for_timeout(5000)
                else:
                    raise e
            
            # Cloudflare Challenge Resolution Loop (Max 15s)
            for i in range(3):
                try:
                    content = await page.evaluate("() => document.body ? document.body.innerText : ''")
                    if "checking your browser" in content.lower() or "verify you are human" in content.lower() or "enable cookies" in content.lower():
                        print(f"  [!] Cloudflare challenge detected (Attempt {i+1}). Waiting 5s...")
                        await page.wait_for_timeout(5000)
                    else:
                        break
                except Exception:
                    # If evaluation fails during redirect, wait and retry
                    await page.wait_for_timeout(2000)
            
            # Final wait for network and content rendering
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            
            # Extract content
            content = await page.evaluate("() => document.body ? document.body.innerText : ''")
            
            if len(content.strip()) > 200:
                return {"url": url, "text": " ".join(content.split())}
                
        except Exception as e:
            print(f"  [!] Error crawling {url}: {e}")
        finally:
            await page.close()
        return None

    def chunk_text(self, text, url, chunk_size=400):
        tokens = self.enc.encode(text)
        chunks = []
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.enc.decode(chunk_tokens)
            chunks.append({"url": url, "text": chunk_text})
        return chunks

    async def build_index(self):
        print(f"[{self.domain}] Hunting for sitemaps...")
        
        # We still use aiohttp for the initial sitemap XML fetch as it's usually not protected by the same JS challenge
        urls = await self._fetch_sitemap_urls()
        
        if not urls:
            print(f"[{self.domain}] No sitemap found. Falling back to homepage-only RAG.")
            urls = [self.base_url]

        print(f"[{self.domain}] Found {len(urls)} target URLs. Initializing Stealth Playwright Crawler...")

        crawled_data = []
        
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            # Launch stealth-like browser
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            # We process in small chunks to avoid overloading the browser context
            chunk_size = 5
            for i in range(0, len(urls), chunk_size):
                batch_urls = urls[i:i + chunk_size]
                print(f"  [+] Crawling batch {i//chunk_size + 1}: {len(batch_urls)} pages...")
                
                tasks = [self._fetch_page(context, url) for url in batch_urls]
                results = await asyncio.gather(*tasks)
                crawled_data.extend([r for r in results if r])
                
                # Small cool-down between batches
                await asyncio.sleep(1)

            await browser.close()
            
        print(f"[{self.domain}] Successfully crawled and cleaned {len(crawled_data)} pages via Playwright.")
        
        # Chunking
        all_chunks = []
        for page in crawled_data:
            all_chunks.extend(self.chunk_text(page["text"], page["url"]))
            
        print(f"[{self.domain}] Generated {len(all_chunks)} semantic knowledge chunks. Vectorizing...")
        
        if not all_chunks:
            print("No text chunks generated. Aborting RAG build.")
            return False

        # Get embeddings in batches (OpenAI allows max 2048 at a time usually, we do 500)
        embeddings = []
        batch_size = 500
        for i in range(0, len(all_chunks), batch_size):
            batch = [c["text"] for c in all_chunks[i:i+batch_size]]
            resp = self.sync_client.embeddings.create(input=batch, model="text-embedding-3-small")
            embeddings.extend([emb.embedding for emb in resp.data])
            
        embeddings_np = np.array(embeddings).astype('float32')
        dimension = embeddings_np.shape[1]
        
        # Build FAISS index (Inner Product for cosine similarity since OpenAI returns normalized vectors)
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings_np)
        
        faiss.write_index(index, self.faiss_index_path)
        with open(self.chunks_data_path, "w") as f:
            json.dump(all_chunks, f)
            
        print(f"[{self.domain}] Vector Database built and saved to {self.output_dir}.")
        return True

    def query_knowledge_base(self, query: str, top_k: int = 5) -> list:
        """Retrieves and returns the most relevant chunks from the site for the given query."""
        if not os.path.exists(self.faiss_index_path) or not os.path.exists(self.chunks_data_path):
            return []
            
        index = faiss.read_index(self.faiss_index_path)
        with open(self.chunks_data_path, "r") as f:
            chunks_data = json.load(f)
            
        emb_resp = self.sync_client.embeddings.create(input=[query], model="text-embedding-3-small")
        q_emb = np.array([emb_resp.data[0].embedding]).astype('float32')
        
        distances, indices = index.search(q_emb, top_k)
        
        results = []
        for idx in indices[0]:
            if idx < len(chunks_data) and idx != -1:
                results.append(chunks_data[idx])
        return results

if __name__ == "__main__":
    # Test execution
    domain = os.environ.get("PROSPECT_DOMAIN", "sharkeymobility.com")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    rag = DeepCrawlerRAG(domain, output_dir, max_pages=50)
    asyncio.run(rag.build_index())
    
    # Test Query
    print("\n--- Test RAG Query: 'wheelchairs' ---")
    results = rag.query_knowledge_base("What manual wheelchairs do they offer?")
    for i, res in enumerate(results, 1):
        print(f"\nResult {i} (from {res['url']}):\n{res['text'][:200]}...")
