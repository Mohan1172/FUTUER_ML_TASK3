from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
BOOTSTRAP_FLAG = "RESUME_SCREENING_IN_PROJECT_VENV"

def _bootstrap_project_environment() -> None:
    """Re-launch this app using its own venv, installing dependencies if needed."""
    if os.environ.get(BOOTSTRAP_FLAG) == "1":
        return
    if not VENV_PYTHON.exists():
        print("Creating project virtual environment at", VENV_DIR)
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    check = subprocess.run(
        [str(VENV_PYTHON), "-c",
         "import importlib.util,sys; mods=['flask','pandas','sklearn','numpy','pypdf','docx']; "
         "sys.exit(0 if all(importlib.util.find_spec(m) for m in mods) else 1)"],
        cwd=ROOT,
    )
    if check.returncode != 0:
        print("Installing dependencies into the project .venv. This may take a few minutes...")
        install = subprocess.run(
            [str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"], cwd=ROOT
        )
        if install.returncode != 0:
            raise SystemExit("Could not upgrade pip in .venv. Check your internet connection.")
        install = subprocess.run(
            [str(VENV_PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
            cwd=ROOT,
        )
        if install.returncode != 0:
            raise SystemExit("Dependency installation failed. Try double-clicking START_APP.bat.")
    env = os.environ.copy()
    env[BOOTSTRAP_FLAG] = "1"
    raise SystemExit(subprocess.call([str(VENV_PYTHON), str(Path(__file__).resolve())], cwd=ROOT, env=env))

_bootstrap_project_environment()

from flask import Flask, render_template, request, send_file
import pandas as pd

from resume_screening import (
    DEFAULT_SKILLS,
    extract_text_from_upload,
    screen_resumes,
    normalize_skill_list,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB total request limit
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
LAST_RESULTS = None


@app.get("/")
def index():
    return render_template(
        "index.html",
        default_skills=", ".join(DEFAULT_SKILLS),
        results=None,
        error=None,
        form_data={},
    )


@app.post("/screen")
def screen():
    global LAST_RESULTS
    job_description = request.form.get("job_description", "").strip()
    skills_text = request.form.get("skills", ", ".join(DEFAULT_SKILLS))
    required_text = request.form.get("required_skills", "")
    preferred_text = request.form.get("preferred_skills", "")
    try:
        skill_weight = float(request.form.get("skill_weight", "65")) / 100.0
        skill_weight = min(1.0, max(0.0, skill_weight))
    except ValueError:
        skill_weight = 0.65

    form_data = {
        "job_description": job_description,
        "skills": skills_text,
        "required_skills": required_text,
        "preferred_skills": preferred_text,
        "skill_weight": int(skill_weight * 100),
    }

    if not job_description:
        return render_template("index.html", default_skills=", ".join(DEFAULT_SKILLS),
                               results=None, error="Please paste a job description.", form_data=form_data), 400

    uploads = request.files.getlist("resumes")
    uploads = [f for f in uploads if f and f.filename]
    if not uploads:
        return render_template("index.html", default_skills=", ".join(DEFAULT_SKILLS),
                               results=None, error="Please upload at least one resume file.", form_data=form_data), 400

    skills = normalize_skill_list(skills_text)
    if not skills:
        return render_template("index.html", default_skills=", ".join(DEFAULT_SKILLS),
                               results=None, error="Please provide at least one skill.", form_data=form_data), 400

    resume_items = []
    errors = []
    for uploaded in uploads:
        suffix = Path(uploaded.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            errors.append(f"{uploaded.filename}: unsupported file type. Use PDF, DOCX, or TXT.")
            continue
        try:
            content = uploaded.read()
            text = extract_text_from_upload(uploaded.filename, content)
            if not text.strip():
                errors.append(f"{uploaded.filename}: no readable text found. Scanned PDFs need OCR first.")
            else:
                resume_items.append({"filename": Path(uploaded.filename).name, "text": text})
        except Exception as exc:
            errors.append(f"{uploaded.filename}: could not read file ({exc}).")

    if not resume_items:
        message = "No readable resumes were found. " + " ".join(errors)
        return render_template("index.html", default_skills=", ".join(DEFAULT_SKILLS),
                               results=None, error=message, form_data=form_data), 400

    try:
        results_df = screen_resumes(
            job_description=job_description,
            resumes=resume_items,
            skills=skills,
            required_skills=normalize_skill_list(required_text),
            preferred_skills=normalize_skill_list(preferred_text),
            skill_weight=skill_weight,
        )
    except Exception as exc:
        return render_template("index.html", default_skills=", ".join(DEFAULT_SKILLS),
                               results=None, error=f"Screening failed: {exc}", form_data=form_data), 500

    LAST_RESULTS = results_df.copy()
    results = results_df.to_dict(orient="records")
    return render_template(
        "index.html",
        default_skills=", ".join(DEFAULT_SKILLS),
        results=results,
        error=(" ".join(errors) if errors else None),
        form_data=form_data,
    )


@app.get("/download-results")
def download_results():
    global LAST_RESULTS
    if LAST_RESULTS is None or LAST_RESULTS.empty:
        return "No screening results yet. Return to the home page and screen resumes first.", 404
    handle = tempfile.NamedTemporaryFile(prefix="resume_screening_", suffix=".csv", delete=False)
    path = Path(handle.name)
    handle.close()
    LAST_RESULTS.to_csv(path, index=False, encoding="utf-8-sig")
    return send_file(path, as_attachment=True, download_name="resume_screening_results.csv", mimetype="text/csv")


@app.errorhandler(413)
def too_large(_error):
    return "The uploaded files are too large. Please upload files with a combined size below 25 MB.", 413


if __name__ == "__main__":
    # Open the browser automatically when launched from VS Code or START_APP.bat.
    import threading
    import webbrowser

    url = "http://127.0.0.1:5000"
    threading.Timer(1.2, lambda: webbrowser.open_new_tab(url)).start()
    # Local development server; use a production WSGI server for public deployment.
    app.run(host="127.0.0.1", port=5000, debug=False)
