from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
class Match:
    def __init__(self, resume_text, job_text):
        self.resume_text = resume_text
        self.job_text = job_text

    def tfidf_match(self, top_n=10):
        documents = [self.resume_text, self.job_text] #List of documents to analyze; the first is the resume, the second is the job description.
        vectorizer = TfidfVectorizer(stop_words='english')   #object to hold ["api", "aws", "docker", "flask", "python", ...]
        tfidf_matrix = vectorizer.fit_transform(documents)   # fittransform to convert the documents into a TF-IDF matrix ["api", "aws", "docker", "flask", "python", ...] and their corresponding TF-IDF weights for each document. The resulting matrix has two rows (one for the resume and one for the job description) and columns corresponding to each unique term in the combined vocabulary of both documents. Each cell contains the TF-IDF weight of that term in that document.
        cosine_sim = (tfidf_matrix * tfidf_matrix.T).A #(cosine_sim[0][1] and cosine_sim[1][0]) represent the similarity between the resume and the job description.
        terms = vectorizer.get_feature_names_out() #Returns an array of all vocabulary terms used by the vectorizer.
        resume_vector = tfidf_matrix[0].toarray().ravel() # Extracts the resume’s TF-IDF row from the matrix and converts it into a 1-D array.[0.1, 0.0, 0.4, …]
        job_vector = tfidf_matrix[1].toarray().ravel() #a 1-D array of TF-IDF importance weights for each vocabulary term in the job description [0.62, 0.41, 0.00, 0.18, ...] 
        job_sorted_index = np.argsort(job_vector)[::-1] #sorts the indices of the job vector in descending order based on their TF-IDF weights,
                                                        #so that the most important terms for the job description are at the beginning of the list.
        similarity_score = cosine_sim[0][1] #Stores the overall similarity score between the resume and job description. either 0 they share practically nothing or 1 they are very similar

        overlap = []
        missing = []
        for x in job_sorted_index:
                if job_vector[x] == 0:
                    break  # no more meaningful job terms

                term = terms[x] #term corresponding to the current index in the sorted job vector

                if resume_vector[x] > 0:
                    overlap.append(term) #term is present in both resume and job description (overlap)
                else:
                    missing.append(term) #term is important in the job description but missing from the resume (missing)

                if len(overlap) >= top_n and len(missing) >= top_n:
                    break

        return {
                "similarity": float(similarity_score),
                "overlap_keywords": overlap[:top_n],
                "missing_keywords": missing[:top_n],
            }
#normalize job description for better matching via tf-idf