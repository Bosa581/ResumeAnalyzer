from urllib.parse import urlparse
from pdfminer.high_level import extract_text
from flask import Flask, flash, session, request, redirect, url_for, render_template
import requests
import secrets
from match import Match
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import re
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

app_data = {
    "resume_raw_text": "",
    "job_text": "",
    "resume_preview": "",
    "job_preview": "",
    "job_extract_mode": "",
    "job_url": "",
    "match_result": None,
}
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
    app_data["resume_raw_text"] = text
    return text


# HTML -> visible text (BeautifulSoup)
def bs4_visible_text_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Remove obvious noise
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    # Try to locate job-relevant sections
    keywords = ["responsibilities", "requirements", "qualifications", "about", "job"]

    sections = []

    for tag in soup.find_all(["h1", "h2", "h3", "strong"]):
        header_text = tag.get_text().lower()

        if any(k in header_text for k in keywords):
            # collect next siblings (content under that section)
            sibling = tag.find_next_sibling()
            count = 0

            while sibling and count < 10:
                text = sibling.get_text(" ", strip=True)
                if text:
                    sections.append(text)
                sibling = sibling.find_next_sibling()
                count += 1

    # fallback if nothing found
    if not sections:
        elements = soup.find_all(["p", "li"])
        sections = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]

    text = " ".join(sections)

    return text


# Fetch HTML via requests
def fetch_html_requests(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
    return resp.text or "", resp.status_code


# Fetch HTML via browser render (Playwright)
def fetch_html_rendered(url: str):
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
def extract_text_from_url(url: str):
    """
    Returns (extracted_text, mode)
      mode: 'requests' or 'rendered'
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
    if len(text) >= 300 and "cookie" not in text.lower():
        return text, "requests"

    # Attempt 2: render JS and parse
    rendered_html = fetch_html_rendered(url)
    rendered_text = bs4_visible_text_from_html(rendered_html)

    if len(rendered_text) < 300:
        raise ValueError("Page fetched but meaningful text not found")

    return rendered_text, "rendered"  # returns (job_text, mode)


# normalize job description for better matching via tf-idf
def normalize_text(text):
    text = text.lower()

    # Preserve important technical tokens
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

# Routes
@app.route('/')
def index():
    return render_template(
        'index.html',
        resume_uploaded=bool(app_data.get("resume_raw_text")),
        job_loaded=bool(app_data.get("job_text")),
        resume_preview=app_data.get("resume_preview", ""),
        job_preview=app_data.get("job_preview", ""),
        job_extract_mode=app_data.get("job_extract_mode", ""),
        match_result=app_data.get("match_result"),
        job_url=app_data.get("job_url", ""),
    )

@app.route('/analyze', methods=['POST'])
def analyze():
    uploaded_file = request.files.get("resume_file")

    if uploaded_file is None or uploaded_file.filename == "":
        flash("No resume uploaded.")
        return redirect(url_for('index'))

    resume_text = extract_text_from_pdf(uploaded_file)
    app_data["resume_preview"] = resume_text[:1000]

    return redirect(url_for('index'))


@app.route('/url_analyze', methods=['POST'])
def url_analyze():
    raw_job_url = request.form.get('job_url', '').strip()

    if raw_job_url == "":
        flash("No job URL entered.")
        return redirect(url_for('index'))

    job_url = normalize_url(raw_job_url)

    if not is_valid_url(job_url):
        flash("Please enter a valid job URL.")
        return redirect(url_for('index'))

    try:
        job_text, mode = extract_text_from_url(job_url)
        app_data["job_text"] = job_text
        app_data["job_extract_mode"] = mode
        app_data["job_preview"] = job_text[:1000]
        app_data["job_url"] = raw_job_url
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('index'))

    return redirect(url_for('index'))

def extract_keywords(text, top_n=20):
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1,2),
        max_features=1000
    )

    tfidf = vectorizer.fit_transform([text])
    scores = tfidf.toarray()[0]
    terms = vectorizer.get_feature_names_out()

    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)

    return [term for term, _ in ranked[:top_n]]

@app.route('/score_match', methods=['POST'])
def score_match():
    resume_text = app_data.get("resume_raw_text", "")
    job_text = app_data.get("job_text", "")

    if not job_text:
        flash("Job description is missing for matching.")
        return redirect(url_for('index'))
    if not resume_text:
        flash("Resume text is empty.")
        return redirect(url_for('index'))

    normalized_resume = normalize_text(resume_text)
    normalized_job = normalize_text(job_text)

    matcher = Match(normalized_resume, normalized_job)
    match_result = matcher.tfidf_match(top_n=10)

    app_data["match_result"] = match_result

    return redirect(url_for('index'))


@app.route('/clear', methods=['POST'])
@app.route('/clear', methods=['POST'])
def clear():
    app_data["resume_raw_text"] = ""
    app_data["job_text"] = ""
    app_data["resume_preview"] = ""
    app_data["job_preview"] = ""
    app_data["job_extract_mode"] = ""
    app_data["job_url"] = ""
    app_data["match_result"] = None

    flash("Session cleared.")
    return redirect(url_for('index'))


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