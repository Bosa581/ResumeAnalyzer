# Resume Analyzer

Resume Analyzer is a **Python + Flask web application** that helps users compare a resume against a job description using natural language processing.

Instead of relying on screenshots or manual review, this tool:
* Extracts text from PDF resumes.
* Fetches and parses text from job description URLs.
* Normalizes and vectorizes text using TF-IDF.
* Computes cosine similarity to score how well a resume matches a job description.
* Highlights keywords that overlap and those that are missing.

## Features

**Upload Resume & Provide Job Description**  
Users upload a PDF resume and enter a job posting URL. The app extracts text from both and runs similarity matching.

**TF-IDF + Cosine Similarity Scoring**  
The core matching engine uses `TfidfVectorizer` from scikit-learn to compute similarity and extract meaningful keywords. :contentReference[oaicite:1]{index=1}

**Two-Stage URL Extraction**  
The app first attempts to get HTML via `requests` and parse with BeautifulSoup. If that yields insufficient text, it uses Playwright to render JavaScript-heavy pages and retry extraction. :contentReference[oaicite:2]{index=2}

## Tech Stack

* Python 3.x
* Flask (web framework)
* scikit-learn (TF-IDF + cosine similarity)
* pdfminer (PDF text extraction)
* BeautifulSoup + Playwright (job description extraction)
* HTML + Jinja2 templates (UI)

## How to Run Locally

1. Clone the repo:
```bash
git clone https://github.com/Bosa581/ResumeAnalyzer.git
cd ResumeAnalyzer

## Instal dependencies
pip install -r requirements.txt

## Run
python. app.py

Navigate to http://127.0.0.1:5000 in your browser and upload a resume + job posting URL.

Next Improvements

Add .docx resume support

Add ranking & downloadable reports

Deploy to the cloud (Render, Railway, etc.)


---

## Strong Resume Bullet Point for This Project

Here’s a polished bullet you can drop directly into your resume under a “Projects” or “Experience” section:

**Resume Analyzer (Python · Flask · NLP)**  
• Built a Flask-based web application that extracts resume text from PDFs and job descriptions from URLs, then computes a similarity score using TF-IDF vectorization and cosine similarity to quantify resume–job fit  
• Developed a text normalization and processing pipeline that feeds into a custom matching engine to identify overlapping and missing keywords between resume and job description  
• Integrated two-stage HTML extraction (requests + Playwright) and session-based workflow for seamless user interaction and scoring results

---

## Why this wording works

- It describes **concrete technologies** you actually used (Flask, TF-IDF, cosine similarity). :contentReference[oaicite:3]{index=3}  
- It doesn’t over-claim concurrency or scalability (you don’t have a threaded server or async yet).  
- It signals **full stack systems thinking** with text processing, web UI, backend logic, and matching engine.  
- It’s specific enough to pass technical resume parsers and human reviewers alike.

---

If you want, I can help you write a **README badge set** (e.g., build status, license, tech stack icons) or draft a **project summary paragraph** for your LinkedIn using this content.
::contentReference[oaicite:4]{index=4}