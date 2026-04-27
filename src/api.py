import os
import sys
import asyncio
import subprocess
import json
from fastapi import FastAPI, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)
key = os.environ.get("OPENAI_API_KEY", "")
if key:
    print(f" [+] API Key Loaded: {key[:10]}...{key[-4:]} (Length: {len(key)})")
else:
    print(" [!] WARNING: No OPENAI_API_KEY found in environment!")

app = FastAPI(title="TrafficRadius Prospect Audit Generator")

# Build absolute paths for static elements
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")
# Sessions are mounted under /output/sessions/ in the filesystem, which is already covered by /output mount

class AuditRequest(BaseModel):
    domain: str
    company_name: str

# In-memory "database" to track status and logs
jobs = {}
job_logs = {}
history_store = []

async def run_audit_job(job_id: str, domain: str, company: str):
    """Background task to run the pipeline visually via subprocess."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["message"] = "Starting audit pipeline..."
    job_logs[job_id] = []
    
    # The instruction implies the script path and cwd might change relative to BASE_DIR
    # Assuming the user wants to run the script from the parent directory (where .env is)
    # and the script itself is now in a 'src' subdirectory relative to that parent.
    # This means BASE_DIR is 'api', and the script is in 'src' relative to the project root.
    project_root_dir = os.path.join(BASE_DIR, "..")
    script_path = os.path.join(project_root_dir, "src", "langgraph_orchestrator.py")
    
    # Create unique session directory
    session_dir = os.path.join(OUTPUT_DIR, "sessions", job_id)
    os.makedirs(session_dir, exist_ok=True)
    jobs[job_id]["output_dir"] = session_dir

    # Use venv python if available, otherwise fallback to current sys.executable
    venv_python_win = os.path.join(project_root_dir, "venv", "Scripts", "python.exe")
    venv_python_nix = os.path.join(project_root_dir, "venv", "bin", "python")
    
    if os.path.exists(venv_python_win):
        python_exe = venv_python_win
    elif os.path.exists(venv_python_nix):
        python_exe = venv_python_nix
    else:
        python_exe = sys.executable

    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        # On Windows, using shell is often more reliable for finding python/venv
        # Construct the command string properly for the shell
        cmd = f'"{python_exe}" -u "{script_path}" "{domain}" "{company}" "us" "{session_dir}" "{job_id}"'
        print(f" [+] Launching Subprocess: {cmd}")
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=project_root_dir,
            env=env
        )
        
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=15.0)
                if not line:
                    break
                decoded_line = line.decode('utf-8', errors='replace').strip()
                if decoded_line:
                    print(f" [Subprocess] {decoded_line}") # Log to console for debugging
                    job_logs[job_id].append(decoded_line)
            except asyncio.TimeoutError:
                pass
                
        await process.wait()
        
        if process.returncode == 0:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = "Audit completed successfully."
        else:
            err_msg = f"Pipeline failed with exit code {process.returncode}"
            print(f" [!] {err_msg}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = err_msg
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"API Error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the main frontend UI."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/start-audit")
async def start_audit(domain: str = Form(...), company: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    import uuid
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "starting", "message": "Initializing...", "domain": domain}
    job_logs[job_id] = ["Initializing LangGraph Orchestrator..."]
    
    background_tasks.add_task(run_audit_job, job_id, domain, company)
    return JSONResponse({"job_id": job_id})

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    
    response_data = jobs[job_id].copy()
    # Add relative paths for front-end access if job is completed and file exists.
    if response_data["status"] == "completed":
        session_dir = os.path.join(OUTPUT_DIR, "sessions", job_id)
        candidates = {
            "docx": ("deliverables", "Strategy_Document.docx"),
            "xlsx": ("deliverables", "12_Month_Action_Plan.xlsx"),
            "pptx": ("deliverables", "Master_Presentation.pptx"),
            "scorecard": ("charts", "integrated_scorecard.png"),
        }
        deliverables = {}
        availability = {}
        for key, parts in candidates.items():
            abs_path = os.path.join(session_dir, *parts)
            exists = os.path.exists(abs_path)
            availability[key] = exists
            if exists:
                deliverables[key] = f"/output/sessions/{job_id}/{'/'.join(parts)}"
        response_data["deliverables"] = deliverables
        response_data["deliverables_available"] = availability
    return JSONResponse(response_data)

@app.get("/api/stream-logs/{job_id}")
async def stream_logs(job_id: str):
    """Server-Sent Events endpoint for real-time terminal logs."""
    async def log_generator():
        last_idx = 0
        while True:
            if job_id not in job_logs:
                yield f"data: {{\"log\": \"[System Error] Job context lost.\"}}\n\n"
                break
                
            current_logs = job_logs[job_id]
            if last_idx < len(current_logs):
                for i in range(last_idx, len(current_logs)):
                    yield f"data: {json.dumps({'log': current_logs[i]})}\n\n"
                last_idx = len(current_logs)
            
            # Check if job is done
            if job_id in jobs and jobs[job_id]["status"] in ["completed", "failed"]:
                # Yield any final logs that might have slipped through
                if last_idx < len(job_logs[job_id]):
                    for i in range(last_idx, len(job_logs[job_id])):
                        yield f"data: {json.dumps({'log': job_logs[job_id][i]})}\n\n"
                yield f"data: {{\"done\": true, \"status\": \"{jobs[job_id]['status']}\"}}\n\n"
                break
                
            await asyncio.sleep(0.5)
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/api/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """Securely serves deliverables with multi-path fallback."""
    session_dir = os.path.join(OUTPUT_DIR, "sessions", job_id)
    file_map = {
        "docx": "deliverables/Strategy_Document.docx",
        "xlsx": "deliverables/12_Month_Action_Plan.xlsx",
        "pptx": "deliverables/Master_Presentation.pptx",
        "scorecard": "charts/integrated_scorecard.png"
    }
    
    if file_type not in file_map:
        return JSONResponse({"error": "Invalid file type"}, status_code=400)
    
    # 1. Try Session Directory (Active Run)
    file_path = os.path.join(session_dir, file_map[file_type])
    
    # 2. Try Archive Directory (History Vault)
    if not os.path.exists(file_path):
        archives_dir = os.path.join(OUTPUT_DIR, "archives")
        # UUID Match
        archive_path = os.path.join(archives_dir, job_id, os.path.basename(file_map[file_type]))
        
        if os.path.exists(archive_path):
            file_path = archive_path
        else:
            # Timestamp Fallback (Scan all folders for a match)
            # Some audits are named YYYYMMDD_HHMMSS_domain
            print(f" [!] Job-specific archive not found for {job_id}. Scanning vault fallbacks...")
            found_fallback = False
            if os.path.exists(archives_dir):
                for folder in os.listdir(archives_dir):
                    # Check if the metadata inside this folder matches our job_id
                    meta_path = os.path.join(archives_dir, folder, "metadata.json")
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r") as f:
                                meta = json.load(f)
                                if meta.get("archive_id") == job_id:
                                    # This is the one!
                                    target_p = os.path.join(archives_dir, folder, os.path.basename(file_map[file_type]))
                                    if os.path.exists(target_p):
                                        file_path = target_p
                                        found_fallback = True
                                        break
                        except: pass
            
            if not found_fallback:
                print(f" [!] CRITICAL: PPTX download failed. job_id={job_id}, type={file_type}. Not in sessions or archives.")
                return JSONResponse({"error": "File not found"}, status_code=404)
            
    print(f" [+] Serving download: {file_path}")
        
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )

@app.get("/api/history")
async def get_history():
    """Returns the history of completed audits from the vault."""
    archives_dir = os.path.join(OUTPUT_DIR, "archives")
    if not os.path.exists(archives_dir):
        return JSONResponse({"history": []})
        
    history = []
    for folder in os.listdir(archives_dir):
        meta_path = os.path.join(archives_dir, folder, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    history.append(json.load(f))
            except Exception:
                pass
                
    # Sort newest first
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return JSONResponse({"history": history})

if __name__ == "__main__":
    import uvicorn
    # Create static dir if not exists
    os.makedirs(STATIC_DIR, exist_ok=True)
    # Disable reload on Windows to prevent "Bad file descriptor" errors during background tasks
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
