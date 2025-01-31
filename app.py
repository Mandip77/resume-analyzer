from flask import Flask, request, jsonify
import spacy
import pdfplumber
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["resumeDB"]
collection = db["resumes"]


# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text


# API to analyze resume
@app.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['resume']
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)

    text = extract_text_from_pdf(file_path)
    doc = nlp(text)

    # Extract skills (simple keyword matching)
    skills = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]

    # Save to DB
    collection.insert_one({"filename": file.filename, "skills": skills, "text": text})

    return jsonify({"filename": file.filename, "skills": skills})


if __name__ == '__main__':
    app.run(debug=True)
