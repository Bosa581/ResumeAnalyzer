from flask import Flask,flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import requests #for the api calls
import secrets
#from pdfminer.high_level import extract_text
from flask import render_template
import os

app = Flask(__name__)  # where to look for the html template via url
secret_key = secrets.token_hex(16) 
@app.secret_key = secret_key
@app.route('/')#routes itself to the html file via http://127.0.0.1:5000 
def index():
    return render_template('index.html')
    
#file location for the uploaded resume
Upload_Folder = "C:/Users/orobo/OneDrive/Desktop/Project20/Resume Analyzer/UploadedFile"
Allowed_Extension = {"pdf"}
app.config["Upload_Folder"] = Upload_Folder  # accesses the actual file

@app.route('/handleform', methods=['POST'])
def handle_forms():
    if not (Upload_Folder.split() in Allowed_Extension):  #.split gets the extension of the file uploaded
        flash("Invalid uploaded file. File must be in Pdf format!!")
    return render_template('index.html')  

def upload_file():
    if request.method == 'POST':
        if 'file'  not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename =='':
            return "No selected file"
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config[Upload_Folder], filename))
            return "File uploaded"

#def extract_text(Upload_Folder):

app.run()