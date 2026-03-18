from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class Match:
    def __init__(self, resume_text, job_text):
        self.resume_text = resume_text
        self.job_text = job_text

    def tfidf_match(self, top_n=10):
        documents = [self.resume_text, self.job_text]  
        # List of documents: [resume, job description]

        vectorizer = TfidfVectorizer(stop_words='english')  
        # holds vocabulary like ["api", "aws", "docker", ...]

        tfidf_matrix = vectorizer.fit_transform(documents)  
        # Matrix where each row is a document and each column is a term weighted by TF-IDF importance

        cosine_sim = (tfidf_matrix * tfidf_matrix.T).toarray()  
        # cosine similarity matrix; cosine_sim[0][1] is resume vs job

        terms = vectorizer.get_feature_names_out()  

        resume_vector = tfidf_matrix[0].toarray().ravel()  
        # resume TF-IDF vector

        job_vector = tfidf_matrix[1].toarray().ravel()  
        # job TF-IDF vector

        job_sorted_index = np.argsort(job_vector)[::-1]  
        # sort terms by importance in job description (descending)

        similarity_score = cosine_sim[0][1]  
        # final similarity score between 0 and 1

        overlap = []
        missing = []

        for x in job_sorted_index:
            if job_vector[x] == 0:
                break

            term = terms[x]

            if resume_vector[x] > 0:
                overlap.append(term)  
                # term exists in both resume and job
            else:
                missing.append(term)  
                # term important in job but missing from resume

            if len(overlap) >= top_n and len(missing) >= top_n:
                break

        return {
            "similarity": float(similarity_score),
            "similarity_percent": round(float(similarity_score) * 100, 2),
            "overlap_keywords": overlap[:top_n],
            "missing_keywords": missing[:top_n],
        }