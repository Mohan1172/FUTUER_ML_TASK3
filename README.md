# Resume Screening and Ranking System

A browser-based resume screening application built with Python, Flask, scikit-learn and HTML/CSS. It does not use Streamlit.

## Run it on Windows

1. Download and extract this project ZIP.
2. Double-click **`START_APP.bat`**.
3. On first run, it creates a project-specific `.venv` and installs the required packages. Internet access is needed for this step.
4. Your default browser opens at `http://127.0.0.1:5000`.
5. Paste a job description, customize skills, upload resumes, and click **Screen and rank resumes**.

Do not open `app.py` by double-clicking it in File Explorer; use `START_APP.bat` or VS Code so dependencies and the browser launch are handled correctly.

## Run from VS Code

1. Open the extracted folder in VS Code.
2. Double-click `START_APP.bat` once to set up dependencies, or create `.venv` and install `requirements.txt`.
3. Open `app.py` and click **Run Python File**. The script now creates/uses `.venv` and installs missing packages there before starting the browser app.

Manual setup commands:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Features

- PDF, DOCX, and TXT resume text extraction.
- Resume text cleaning.
- Editable skill dictionary.
- Job-description skill matching.
- Candidate ranking with skill coverage and TF-IDF cosine similarity.
- Required/preferred skill gap reports.
- CSV export.
- Responsive HTML browser interface.

## Scoring

`Overall score = skill-match weight × skill match + remaining weight × TF-IDF cosine similarity`

The default is 65% skill match and 35% text similarity. Scores are text matching indicators, not predictions of job performance.

## Public sharing / deployment

`127.0.0.1` is local to your own computer; other people cannot access it through that address. To make a public URL, deploy this Flask app to a Python hosting provider using a production WSGI server such as Gunicorn (Linux hosts) or Waitress (Windows hosts). Do not expose Flask's built-in development server directly to the public internet.

## Limitations and responsible use

- Scanned image-only PDFs require OCR first.
- Skill detection depends on the supplied skills list and wording.
- Do not use the score as the sole basis for hiring or automatically reject candidates. A person should review every result.
