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
