const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function renderSlides(sessionDir, outputDir) {
    const dataPath = path.join(sessionDir, 'ppt_slides_data.json');
    const templatePath = path.join(__dirname, 'ppt_slide_template.html');
    
    if (!fs.existsSync(dataPath)) {
        console.error(`Error: Data file not found at ${dataPath}`);
        process.exit(1);
    }
    
    const slidesData = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    const templateHtml = fs.readFileSync(templatePath, 'utf8');
    
    const browser = await chromium.launch({
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 2 // Enable High-DPI (Retina) for 4K-ish quality
    });
    const page = await context.newPage();
    
    // Add logging for browser errors
    page.on('console', msg => {
        if (msg.type() === 'error' || msg.type() === 'warn') {
            console.log(` [Browser ${msg.type().toUpperCase()}]: ${msg.text()}`);
        }
    });
    page.on('pageerror', err => {
        console.error(` [Browser Exception]: ${err.message}`);
    });

    const logoPath = path.join(path.dirname(__dirname), 'src', 'static', 'logo.png');
    let logoBase64 = "";
    if (fs.existsSync(logoPath)) {
        logoBase64 = fs.readFileSync(logoPath).toString('base64');
    }

    console.log(`Starting render for ${slidesData.length} slides...`);

    for (let i = 0; i < slidesData.length; i++) {
        const slide = slidesData[i];
        const slideNum = (i + 1).toString().padStart(2, '0');
        
        // V9: Load Component HTML if archetype is present
        if (slide.archetype) {
            const componentPath = path.join(__dirname, 'components', `${slide.archetype}.html`);
            if (fs.existsSync(componentPath)) {
                slide.component_html = fs.readFileSync(componentPath, 'utf8');
            } else {
                console.warn(` [!] Archetype component not found: ${slide.archetype}`);
            }
        }

        await page.setContent(templateHtml);

        // Inject data via DOM manipulation
        await page.evaluate(({ slide, index, totalSlides, logoB64 }) => {
            // 1. Text Mapping (Title, Subtitle, Slide Num)
            const titleEl = document.getElementById('v14-title') || document.getElementById('title');
            const subtitleEl = document.getElementById('v14-subtitle') || document.getElementById('subtitle');
            const slideNumEl = document.getElementById('v14-slide-num') || document.getElementById('slide-num');

            if (titleEl) titleEl.innerText = slide.title || '';
            if (subtitleEl) subtitleEl.innerText = slide.subtitle || '';
            if (slideNumEl) {
                const currentNum = String(index + 1).padStart(2, '0');
                const totalNum = String(totalSlides).padStart(2, '0');
                slideNumEl.innerText = `SLIDE ${currentNum} OF ${totalNum}`;
            }

            // 2. Logo Injection (Legacy & V14)
            if (logoB64) {
                window.logoDataUri = `data:image/png;base64,${logoB64}`;
            }

            // 3. Bullets (Optional - Template may not show them)
            const bulletList = document.getElementById('v15-bullets') || document.getElementById('v14-bullets') || document.getElementById('bullets');
            if (bulletList && slide.bullets) {
                bulletList.innerHTML = slide.bullets
                    .map(b => `<div class="v15-insight-card"><div class="v15-card-dot"></div><div class="v15-card-text">${b}</div></div>`)
                    .join('');
            }
        }, { slide, index: i, totalSlides: slidesData.length, logoB64: logoBase64 });

        // V9: Component Injection (Must happen after setContent and main evaluate)
        if (slide.archetype && slide.component_html) {
            await page.evaluate(({ html, slideData }) => {
                if (typeof window.loadComponent === 'function') {
                    window.loadComponent(html, slideData);
                }
            }, { html: slide.component_html, slideData: slide });
            
            // Wait for component to settle and transitions to finish
            await page.waitForTimeout(1000);
        }

        // Handle Image Path Resolution (relative to sessionDir) for 'image' type visuals
        // This needs to happen AFTER the page.evaluate call sets up the visual type
        // Handle Image Path Resolution (Only if type is image/undefined and visual is provided)
        const isDiagram = ['radar', 'pyramid', 'funnel', 'matrix'].includes(slide.visual_type);
        
        if (!isDiagram && slide.visual) {
            let assetPath = path.join(sessionDir, slide.visual);
            if (fs.existsSync(assetPath)) {
                const imgData = fs.readFileSync(assetPath).toString('base64');
                await page.evaluate(({ b64 }) => {
                    const img = document.getElementById('visual-img');
                    if (img) {
                        img.src = `data:image/png;base64,${b64}`;
                        img.style.display = 'block';
                    }
                    const fb = document.getElementById('visual-fallback');
                    if (fb) fb.style.display = 'none';
                }, { b64: imgData });
            } else {
                console.warn(` [!] Warning: Visual asset not found: ${slide.visual}`);
                await page.evaluate(() => {
                    const img = document.getElementById('visual-img');
                    const fb = document.getElementById('visual-fallback');
                    if (img) img.style.display = 'none';
                    if (fb) fb.style.display = 'flex';
                });
            }
        } else if (!isDiagram && !slide.visual) {
            // No visual provided and not a diagram - ensure fallback is hidden unless it's a layout that needs it
            await page.evaluate(() => {
                const fb = document.getElementById('visual-fallback');
                if (fb) fb.style.display = 'none';
            });
        }

        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000); // Give CSS diagrams extra time to settle
        const screenshotPath = path.join(outputDir, `slide_${slideNum}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(` [+] Rendered slide ${slideNum}: ${screenshotPath}`);
    }

    await browser.close();
    console.log("Render complete.");
}

const sessionDir = process.argv[2];
const outputDir = path.join(sessionDir, 'rendered_slides');

if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

renderSlides(sessionDir, outputDir).catch(err => {
    console.error(err);
    process.exit(1);
});
