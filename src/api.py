import os
import sys
import asyncio
import subprocess
import json
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from .semrush_client import SemrushClient, SemrushAPIError

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

def _blank_usage_summary():
    return {
        "openai_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_openai_cost": 0.0,
        "models_used": [],
        "last_model": None,
    }

def _merge_usage_summary(existing, delta):
    base = dict(_blank_usage_summary())
    if isinstance(existing, dict):
        base.update(existing)
    if not isinstance(delta, dict):
        return base

    base["openai_calls"] = int(base.get("openai_calls", 0) or 0) + int(delta.get("openai_calls", 0) or 0)
    base["input_tokens"] = int(base.get("input_tokens", 0) or 0) + int(delta.get("input_tokens", 0) or 0)
    base["output_tokens"] = int(base.get("output_tokens", 0) or 0) + int(delta.get("output_tokens", 0) or 0)
    base["total_tokens"] = int(base.get("total_tokens", 0) or 0) + int(delta.get("total_tokens", 0) or 0)
    base["estimated_openai_cost"] = round(
        float(base.get("estimated_openai_cost", 0.0) or 0.0) + float(delta.get("estimated_openai_cost", 0.0) or 0.0),
        6,
    )
    models = list(base.get("models_used", []) or [])
    for model in delta.get("models_used", []) or []:
        if model and model not in models:
            models.append(model)
    base["models_used"] = models
    if delta.get("last_model"):
        base["last_model"] = delta.get("last_model")
    return base

def _load_usage_context(session_dir: str):
    market_path = os.path.join(session_dir, "market_intelligence.json")
    if not os.path.exists(market_path):
        return None
    try:
        with open(market_path, "r", encoding="utf-8") as f:
            market = json.load(f)
    except Exception:
        return None

    availability = market.get("availability", {}) or {}
    semrush_mode = str(availability.get("semrush") or "").strip().lower()
    fallback_used = semrush_mode == "fallback_sample"
    api_error_message = availability.get("details") or availability.get("warning") or ""
    return {
        "fallback_sample_used": fallback_used if semrush_mode else None,
        "api_error_message": api_error_message or None,
    }


def _run_log_path(run_dir: str):
    return os.path.join(run_dir, "run_logs.jsonl")


def _detect_log_level(raw_line: str):
    upper = str(raw_line or "").upper()
    if "TRACEBACK" in upper or "EXCEPTION" in upper or "PIPELINE FAILED" in upper:
        return "ERROR"
    if "WARN" in upper or "WARNING" in upper or "RATE LIMIT" in upper:
        return "WARN"
    if "[!]" in upper or " FAILED" in upper or "FAILED:" in upper:
        return "ERROR"
    if "[SUCCESS]" in upper or "[+]" in upper or " SUCCESS" in upper:
        return "SUCCESS"
    if "[PROGRESS]" in upper or "[NODE]" in upper:
        return "PROCESS"
    return "INFO"


def _detect_log_source(raw_line: str):
    text = str(raw_line or "")
    upper = text.upper()
    if "SEMRUSH" in upper:
        return "SEMrush"
    if "VISION" in upper or "CRO" in upper or "SCREENSHOT" in upper:
        return "Vision-CRO"
    if "RAG" in upper or "FAISS" in upper or "EMBEDDING" in upper:
        return "RAG"
    if "TECHNICAL" in upper or "SCHEMA" in upper or "ROBOTS" in upper or "SITEMAP" in upper:
        return "Tech-Audit"
    if "STRATEGY" in upper or "GPT-4O" in upper or "NARRATIVE" in upper:
        return "Strategist"
    if "PPT" in upper or "DOCX" in upper or "XLSX" in upper or "DELIVERABLE" in upper:
        return "Deliverables"
    if "[PROGRESS]" in upper or "[NODE]" in upper or "[+]" in upper or "[!]" in upper:
        return "orchestrator"
    return "system"


def _make_log_record(raw_line: str, index: Optional[int] = None, timestamp: Optional[str] = None):
    text = str(raw_line or "").rstrip("\r\n")
    return {
        "index": index,
        "timestamp": timestamp or datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": _detect_log_level(text),
        "source": _detect_log_source(text),
        "message": text,
        "raw": text,
    }


def _append_job_log(job_id: str, raw_line: str, session_dir: Optional[str] = None):
    records = job_logs.setdefault(job_id, [])
    record = _make_log_record(raw_line, index=len(records))
    records.append(record)
    if session_dir:
        try:
            with open(_run_log_path(session_dir), "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=True) + "\n")
        except Exception:
            pass
    return record


def _load_persisted_run_logs(path: str):
    if not os.path.exists(path):
        return []
    logs = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    item = _make_log_record(line, index=idx)
                if not isinstance(item, dict):
                    item = _make_log_record(str(item), index=idx)
                raw = item.get("raw") or item.get("message") or ""
                item["raw"] = raw
                item["message"] = item.get("message") or raw
                item["timestamp"] = item.get("timestamp") or datetime.now().strftime("%H:%M:%S.%f")[:-3]
                item["level"] = item.get("level") or _detect_log_level(raw)
                item["source"] = item.get("source") or _detect_log_source(raw)
                item["index"] = idx if item.get("index") is None else item.get("index")
                logs.append(item)
    except Exception:
        return []
    return logs


def _load_archive_metadata(job_id: str):
    meta_path = os.path.join(OUTPUT_DIR, "archives", job_id, "metadata.json")
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_run_logs(job_id: str):
    session_dir = (jobs.get(job_id) or {}).get("output_dir") or os.path.join(OUTPUT_DIR, "sessions", job_id)
    for candidate in (_run_log_path(session_dir), _run_log_path(os.path.join(OUTPUT_DIR, "archives", job_id))):
        logs = _load_persisted_run_logs(candidate)
        if logs:
            return logs

    logs = []
    for idx, item in enumerate(job_logs.get(job_id, [])):
        if isinstance(item, dict):
            record = dict(item)
            raw = record.get("raw") or record.get("message") or ""
            record["raw"] = raw
            record["message"] = record.get("message") or raw
            record["timestamp"] = record.get("timestamp") or datetime.now().strftime("%H:%M:%S.%f")[:-3]
            record["level"] = record.get("level") or _detect_log_level(raw)
            record["source"] = record.get("source") or _detect_log_source(raw)
            record["index"] = idx if record.get("index") is None else record.get("index")
            logs.append(record)
        else:
            logs.append(_make_log_record(item, index=idx))
    return logs


def _collect_session_deliverables(session_dir: str):
    candidates = {
        "docx": ("deliverables", "Strategy_Document.docx"),
        "xlsx": ("deliverables", "12_Month_Action_Plan.xlsx"),
        "pptx": ("deliverables", "Master_Presentation.pptx"),
    }
    deliverables = {}
    availability = {}
    for key, parts in candidates.items():
        abs_path = os.path.join(session_dir, *parts)
        exists = os.path.exists(abs_path)
        availability[key] = exists
        if exists:
            deliverables[key] = f"/output/sessions/{os.path.basename(session_dir)}/{'/'.join(parts)}"
    return deliverables, availability

async def run_audit_job(job_id: str, domain: str, company: str, competitors: Optional[List[str]] = None):
    """Background task to run the pipeline visually via subprocess."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["message"] = "Starting audit pipeline..."
    jobs[job_id]["usage"] = _blank_usage_summary()
    jobs[job_id]["usage_context"] = None
    jobs[job_id]["deliverables"] = {}
    jobs[job_id]["deliverables_available"] = {"docx": False, "xlsx": False, "pptx": False}
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
    _append_job_log(job_id, "Initializing LangGraph Orchestrator...", session_dir)
    competitor_file = os.path.join(session_dir, "user_competitors.json")
    if competitors:
        with open(competitor_file, "w", encoding="utf-8") as f:
            json.dump({"competitors": competitors}, f, indent=2)
    else:
        competitor_file = ""

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
        stream_completed = False
        process = None

        def finalize_when_deliverables_ready():
            nonlocal stream_completed
            if stream_completed:
                return
            deliverables, availability = _collect_session_deliverables(session_dir)
            if all(availability.values()):
                jobs[job_id]["deliverables"] = deliverables
                jobs[job_id]["deliverables_available"] = availability
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["message"] = "Deliverables ready for download."
                stream_completed = True
        
        # On Windows, using shell is often more reliable for finding python/venv
        # Construct the command string properly for the shell
        cmd_parts = [
            f'"{python_exe}"',
            "-u",
            f'"{script_path}"',
            f'"{domain}"',
            f'"{company}"',
            '"us"',
            f'"{session_dir}"',
            f'"{job_id}"',
        ]
        if competitor_file:
            cmd_parts.append(f'"{competitor_file}"')
        cmd = " ".join(cmd_parts)
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
                line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                if not line:
                    break
                decoded_line = line.decode('utf-8', errors='replace').strip()
                if decoded_line:
                    if decoded_line.startswith("[USAGE] "):
                        try:
                            payload = json.loads(decoded_line[len("[USAGE] "):].strip())
                            if payload.get("event") == "usage_delta":
                                jobs[job_id]["usage"] = _merge_usage_summary(jobs[job_id].get("usage"), payload)
                            elif isinstance(payload, dict):
                                jobs[job_id]["usage"] = payload
                        except Exception:
                            pass
                        continue
                    print(f" [Subprocess] {decoded_line}") # Log to console for debugging
                    if not stream_completed:
                        _append_job_log(job_id, decoded_line, session_dir)
                    jobs[job_id]["usage_context"] = _load_usage_context(session_dir) or jobs[job_id].get("usage_context")
                    finalize_when_deliverables_ready()
                    if stream_completed:
                        break
            except asyncio.TimeoutError:
                finalize_when_deliverables_ready()
                if stream_completed:
                    break
                
        await process.wait()
        finalize_when_deliverables_ready()
        jobs[job_id]["usage_context"] = _load_usage_context(session_dir) or jobs[job_id].get("usage_context")
        deliverables, availability = _collect_session_deliverables(session_dir)
        jobs[job_id]["deliverables"] = deliverables
        jobs[job_id]["deliverables_available"] = availability

        archive_status = None
        archive_meta_path = os.path.join(OUTPUT_DIR, "archives", job_id, "metadata.json")
        if os.path.exists(archive_meta_path):
            try:
                with open(archive_meta_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                archive_status = metadata.get("status")
                metadata["usage"] = jobs[job_id].get("usage")
                metadata["usage_context"] = jobs[job_id].get("usage_context")
                with open(archive_meta_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
            except Exception:
                pass
        archive_dir = os.path.join(OUTPUT_DIR, "archives", job_id)
        session_log_path = _run_log_path(session_dir)
        if os.path.exists(session_log_path) and os.path.exists(archive_dir):
            try:
                shutil.copy2(session_log_path, _run_log_path(archive_dir))
            except Exception:
                pass
        
        if process.returncode == 0:
            if archive_status == "partial_failure" or not all(availability.values()):
                missing = [name.upper() for name, present in availability.items() if not present]
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["message"] = (
                    f"Audit completed with missing deliverables: {', '.join(missing)}."
                    if missing
                    else "Audit completed with missing deliverables."
                )
            elif jobs[job_id].get("status") != "completed":
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["message"] = "Audit completed successfully."
        else:
            err_msg = f"Pipeline failed with exit code {process.returncode}"
            if jobs[job_id].get("status") != "completed":
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
    return FileResponse(index_path, media_type="text/html")

@app.post("/api/start-audit")
async def start_audit(
    domain: str = Form(...),
    company: str = Form(...),
    competitors: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    import uuid
    job_id = str(uuid.uuid4())
    competitor_list: List[str] = []
    if competitors:
        try:
            parsed = json.loads(competitors)
            if isinstance(parsed, list):
                competitor_list = [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            competitor_list = []

    jobs[job_id] = {
        "status": "starting",
        "message": "Initializing...",
        "domain": domain,
        "company": company,
        "competitors": competitor_list,
        "usage": _blank_usage_summary(),
        "usage_context": None,
    }
    job_logs[job_id] = []
    
    background_tasks.add_task(run_audit_job, job_id, domain, company, competitor_list)
    return JSONResponse({"job_id": job_id})

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    
    response_data = jobs[job_id].copy()
    # Add relative paths for front-end access if job is completed and file exists.
    session_dir = os.path.join(OUTPUT_DIR, "sessions", job_id)
    deliverables, availability = _collect_session_deliverables(session_dir)
    response_data["deliverables"] = deliverables
    response_data["deliverables_available"] = availability
    return JSONResponse(response_data)

@app.get("/api/run-logs/{job_id}")
async def get_run_logs(job_id: str):
    metadata = _load_archive_metadata(job_id)
    status = jobs.get(job_id, {}).get("status") or (metadata or {}).get("status") or "unknown"
    return JSONResponse({
        "job_id": job_id,
        "status": status,
        "logs": _load_run_logs(job_id),
    })

@app.get("/api/semrush-units")
async def get_semrush_units():
    try:
        client = SemrushClient()
        balance = client.get_api_unit_balance()
        remaining_units = int(balance.get("remaining_units", 0) or 0)
        return JSONResponse({
            "available": True,
            "remaining_units": remaining_units,
            "formatted_remaining_units": f"{remaining_units:,}",
            "source": balance.get("source", "live"),
            "label": "remaining",
            "message": "Live SEMrush API balance",
        })
    except (ValueError, SemrushAPIError) as exc:
        return JSONResponse({
            "available": False,
            "remaining_units": None,
            "formatted_remaining_units": None,
            "source": "unavailable",
            "label": "",
            "message": "SEMrush unavailable",
            "details": str(exc),
        })

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
                    record = current_logs[i]
                    if not isinstance(record, dict):
                        record = _make_log_record(record, index=i)
                    else:
                        record = dict(record)
                        record["index"] = i if record.get("index") is None else record.get("index")
                        raw = record.get("raw") or record.get("message") or ""
                        record["raw"] = raw
                        record["message"] = record.get("message") or raw
                        record["level"] = record.get("level") or _detect_log_level(raw)
                        record["source"] = record.get("source") or _detect_log_source(raw)
                    yield f"data: {json.dumps({'log': record['raw'], 'log_entry': record})}\n\n"
                last_idx = len(current_logs)
            
            # Check if job is done
            if job_id in jobs and (
                jobs[job_id]["status"] in ["completed", "failed"]
                or all((jobs[job_id].get("deliverables_available") or {}).values())
            ):
                # Yield any final logs that might have slipped through
                if last_idx < len(job_logs[job_id]):
                    for i in range(last_idx, len(job_logs[job_id])):
                        record = job_logs[job_id][i]
                        if not isinstance(record, dict):
                            record = _make_log_record(record, index=i)
                        else:
                            record = dict(record)
                            record["index"] = i if record.get("index") is None else record.get("index")
                            raw = record.get("raw") or record.get("message") or ""
                            record["raw"] = raw
                            record["message"] = record.get("message") or raw
                            record["level"] = record.get("level") or _detect_log_level(raw)
                            record["source"] = record.get("source") or _detect_log_source(raw)
                        yield f"data: {json.dumps({'log': record['raw'], 'log_entry': record})}\n\n"
                done_status = "completed" if all((jobs[job_id].get("deliverables_available") or {}).values()) else jobs[job_id]["status"]
                yield f"data: {{\"done\": true, \"status\": \"{done_status}\"}}\n\n"
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
