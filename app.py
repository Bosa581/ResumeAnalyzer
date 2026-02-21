from urllib.parse import urlparse
from pdfminer.high_level import extract_text
from flask import Flask, flash, session, request, redirect, url_for, render_template
import requests
import secrets
from match import Match

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# -----------------------------
# URL utilities
# -----------------------------
def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


# PDF extraction (resume)
uploaded_File_Placeholder = None  # Placeholder for uploaded file
def extract_text_from_pdf(uploaded_file):
    text = extract_text(uploaded_file.stream)
    session["resume_raw_text"] = text
    return text
# HTML -> visible text (BeautifulSoup)
def bs4_visible_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


# Fetch HTML via requests
def fetch_html_requests(url: str) -> tuple[str, int]:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
    return resp.text or "", resp.status_code


# Fetch HTML via browser render (Playwright)
def fetch_html_rendered(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")
        page.goto(url, wait_until="networkidle", timeout=30000)
        html = page.content()
        browser.close()
        return html or ""


# Two-stage URL text extraction:
# 1) requests + bs4
# 2) if too short, Playwright render + bs4
def extract_text_from_url(url: str) -> tuple[str, str]:
    """
    Returns (extracted_text, mode)
      mode: 'requests' or 'rendered'

    Raises ValueError for invalid/blocked/unextractable cases.
    """
    if not url:
        raise ValueError("Enter a URL")

    html, status = fetch_html_requests(url)

    # Fail-fast for common protected/invalid cases
    if status in (400, 401, 403, 404):
        raise ValueError(f"HTTP {status}: blocked/invalid/expired page")

    # Attempt 1: parse what we got
    text = bs4_visible_text_from_html(html)

    # Heuristic: if we got enough text, accept it
    if len(text) >= 300:
        return text, "requests"

    # Attempt 2: render JS and parse
    rendered_html = fetch_html_rendered(url)
    rendered_text = bs4_visible_text_from_html(rendered_html)

    if len(rendered_text) < 300:
        raise ValueError("Page fetched but meaningful text not found (JS-rendered, consent page, or blocked)")

    return rendered_text, "rendered" #returns (job_text, mode)

def normalize_description(job_text):  #we are looking for a developer with python's flask with some experince in c++
    lowercase = job_text.lower()
    newlowercase = ""
    empty = " "
    #removing punctuation
    non_punctuation = "abcdefghijklmnopqrstuvwxyz0123456789+.#"
    for x in range(len(lowercase)):
        if lowercase[x] in non_punctuation:
            newlowercase = newlowercase + lowercase[x]
        else:
            newlowercase = newlowercase + empty
    return newlowercase

#normalize resume for better matching via tf-idf
def normalize_resume(resume_text):
    lowercase = resume_text.lower()
    newlowercase = ""
    empty = " "
    #removing punctuation
    non_punctuation = "abcdefghijklmnopqrstuvwxyz0123456789+.#"
    for x in range(len(lowercase)):
        if lowercase[x] in non_punctuation:
            newlowercase = newlowercase + lowercase[x]
        else:
            newlowercase = newlowercase + empty
    return newlowercase

#tf-idf vectorization and matching, it uses cosine similarity to determine how similar 
# the resume is to the job description and returns a similarity score between 0 and 1
#Matrix where each row is a document (resume, job) and each column is a term weighted by TF-IDF importance.
#cosine_sim
#Matrix of cosine similarities between document vectors; cosine_sim[0][1] is the resume-to-job match score.
#shoutout to data mining lol
# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    uploaded_file = request.files.get("resume_file")
    if not uploaded_file:
        flash("No resume uploaded.")
        return redirect(url_for('index'))

    resume_text = extract_text_from_pdf(uploaded_file)
    session["resume_raw_text"] = resume_text

    return f"Resume preview:<br><pre>{resume_text[:2500]}</pre>"

@app.route('/url_analyze', methods=['POST'])
def url_analyze():
    raw_job_url = (request.form.get('job_url') or "").strip()
    job_url = normalize_url(raw_job_url)

    if not is_valid_url(job_url):
        flash("Please enter a valid job URL.")
        return redirect(url_for('index'))

    try:
        job_text, mode = extract_text_from_url(job_url)
        session["job_text"] = job_text #stores job text and mode in session for later use (e.g.,comparision, debugging or display)
        session["job_extract_mode"] = mode
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('index'))

    return f"<pre>{job_text[:2500]}</pre>"

@app.route('/score_match', methods=['POST'])
def score_match():
    #retrieves the raw resume text and raw job tetx from the session, which was stored during the /analyze route after extracting text from the uploaded PDF. 
    # If for some reason it's not found, it defaults to an empty string.
    resume_text = session.get("resume_raw_text", "")
    job_text = session.get("job_text", "") 

    if not resume_text or not job_text:
        flash("Resume or job description missing for matching.")
        return redirect(url_for('index'))

    normalized_resume = normalize_resume(resume_text)
    normalized_job = normalize_description(job_text)

    matcher = Match(normalized_resume, normalized_job)
    match_result = matcher.tfidf_match(top_n=10) #calls the tfidf_match method of the Match class, which computes the similarity score and identifies the top overlapping and missing keywords between the resume and job description. The result is stored in match_result, which is a dictionary containing the similarity score, list of overlapping keywords, and list of missing keywords.
    session["match_result"] = match_result #stores the match result in the session for later use (e.g., display or debugging)
    return redirect(url_for('index')) #redirects the user back to the index page after computing the match score, where the results can be displayed or accessed for debugging.

@app.route('/debug')
def debug():
    resume_preview = session.get("resume_raw_text", "")[:500]
    job_preview = session.get("job_text", "")[:500]
    mode = session.get("job_extract_mode", "N/A")
    return (
        f"<h3>Resume (first 500)</h3><pre>{resume_preview}</pre>"
        f"<h3>Job (first 500) — mode: {mode}</h3><pre>{job_preview}</pre>"
    )

if __name__ == "__main__":
    app.run(debug=True)
