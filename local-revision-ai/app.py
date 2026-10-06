import json
import re
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:1b"

GENERATE_NOTE_PROMPT = """You are an expert educator. Write concise, structured study notes on the following topic.
Include an Overview, Key Concepts, Terminology, and Pros/Cons or Important Formulas.

Topic: """

SUMMARY_PROMPT = "You are a revision helper. Summarize the following notes into clear bullet points highlighting main concepts, key terms, and formulas:\n\n"
EXPLAIN_PROMPT = "Explain the core concepts in these notes simply so a beginner can easily understand them:\n\n"

QUIZ_PROMPT = """You are an exam generator. Create 4 multiple choice questions based strictly on these notes.
Output ONLY a valid JSON array of objects without markdown code blocks.

Format:
[
  {
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answerIndex": 0,
    "explanation": "Brief explanation of why Option A is correct."
  }
]

Notes:
"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    input_text = data.get("notes", "").strip()
    task_type = data.get("task", "summary")

    if not input_text:
        return jsonify({"error": "Please provide notes or a topic name first."}), 400

    if task_type == "generate_note":
        prompt = GENERATE_NOTE_PROMPT + input_text
    elif task_type == "summary":
        prompt = SUMMARY_PROMPT + input_text
    elif task_type == "explain":
        prompt = EXPLAIN_PROMPT + input_text
    else:
        prompt = QUIZ_PROMPT + input_text

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        res_text = response.json().get("response", "")

        if task_type == "quiz":
            # Clean up markdown formatting
            clean_text = res_text.replace("```json", "").replace("```", "").strip()
            
            # Format multi-line JSON blocks into a valid JSON array
            if not clean_text.startswith("["):
                clean_text = "[" + re.sub(r'}\s*\{', '},{', clean_text) + "]"

            try:
                quiz_data = json.loads(clean_text)
                return jsonify({"task": "quiz", "data": quiz_data})
            except Exception:
                return jsonify({"task": "text", "result": res_text})
        
        return jsonify({"task": "text", "result": res_text})

    except Exception as e:
        return jsonify({"error": f"Failed to connect to local AI: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)