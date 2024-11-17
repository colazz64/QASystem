from flask import Flask, request, jsonify, render_template, send_from_directory, session
from transformers import pipeline
import pdfplumber
import os

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "your_secret_key"  # Set a secure key for session management

# Ensure the uploads folder exists
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure app to use the uploads folder
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load models for summarization and QA
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
qa_model = pipeline("question-answering", model="deepset/roberta-base-squad2")

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

# Route for the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route for file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'document' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['document']

    # Validate file extension
    if not file.filename.endswith(('.pdf', '.doc', '.docx', '.txt')):
        return jsonify({"error": "Unsupported file type"}), 400

    # Save the file
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    # Extract text from the file
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        return jsonify({"error": "The uploaded file contains no readable text."}), 400

    # Store the extracted text in the session
    session['document_context'] = text

    # Generate summary
    try:
        truncated_text = text[:1000]  # BART model input limit
        summary = summarizer(truncated_text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
    except Exception as e:
        print(f"Error generating summary: {e}")
        summary = "Summary could not be generated."

    # Suggested questions
    suggested_questions = [
        "What is the main purpose of the document?",
        "Can you summarize the key findings?",
        "What are the next steps outlined in the document?"
    ]

    # Return JSON response
    return jsonify({
        "pdf_url": f"/uploads/{file.filename}",
        "summary": summary,
        "suggested_questions": suggested_questions
    })

# Route for the after-upload page
@app.route('/afterupload', methods=['GET', 'POST'])
def afterupload():
    if request.method == 'GET':
        # Extract data from query parameters for the GET request
        pdf_url = request.args.get('pdf_url')
        summary = request.args.get('summary')
        questions = request.args.get('questions').split('|')  # Split questions back into a list

        # Render the page
        return render_template(
            'afterupload.html',
            pdf_url=pdf_url,
            summary=summary,
            suggested_questions=questions
        )
    
    elif request.method == 'POST':
        # Handle the question submitted via the form
        user_question = request.form.get('question')
        if not user_question:
            return jsonify({"error": "No question provided."}), 400

        # Retrieve the document context from the session
        document_context = session.get('document_context', "")
        if not document_context.strip():
            return jsonify({"error": "No document context available. Please upload a document first."}), 400

        # Use the QA model to generate an answer
        try:
            qa_response = qa_model(question=user_question, context=document_context)
            answer = qa_response.get("answer", "Sorry, I couldn't find an answer to your question.")
        except Exception as e:
            answer = f"An error occurred while processing your question: {str(e)}"

        # Return the answer as JSON
        return jsonify({"answer": answer})

# Route for serving uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5500)
