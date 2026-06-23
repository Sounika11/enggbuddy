from flask import Flask, render_template, request, send_file
from datetime import datetime
from io import BytesIO
from google import genai
import PyPDF2
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
latest_resume_result = ""

# ================= GEMINI CONFIG =================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# ================= UPLOAD FOLDER =================

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= HOME =================

@app.route("/")
def home():

    return render_template("index.html")

# ================= RESUME ANALYZER =================

@app.route("/resume")
def resume():

    return render_template(
        "resume_analyzer.html"
    )

@app.route("/analyze_resume", methods=["POST"])
def analyze_resume():

    uploaded_file = request.files["resume"]

    if uploaded_file.filename == "":
        return "No file selected"

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        uploaded_file.filename
    )

    uploaded_file.save(file_path)

    # PDF TEXT EXTRACTION

    resume_text = ""

    with open(file_path, "rb") as file:

        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:

            text = page.extract_text()

            if text:
                resume_text += text

    # GEMINI PROMPT

    prompt = f"""
You are a professional ATS Resume Analyzer and Career Coach.

Analyze the following resume thoroughly.

Return output EXACTLY in this format:

ATS SCORE: X/10

* PROFESSIONAL SUMMARY
Brief evaluation of the candidate.

TECHNICAL STRENGTHS:
- point
- point
- point

WEAKNESSES:
- point
- point

SKILL GAP ANALYSIS:
Current Skills: Python, Flask, SQL
Recommended Skills: Docker, AWS, Git
Industry Demand Skills: Kubernetes, CI/CD

ATS IMPROVEMENTS:
- point
- point

PROJECT RECOMMENDATIONS:
- project idea
- project idea

CAREER RECOMMENDATIONS:
- recommendation
- recommendation

FINAL VERDICT:
Give a short conclusion on placement readiness.

Resume:
{resume_text}
"""
    
    timestamp = datetime.now().strftime(
        "%d %b %Y | %I:%M %p"
    )

    sections = {}

    ats_score = 0

    grade = "N/A"

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        result = response.text
        sections = {}

        current_heading = "SUMMARY"

        sections[current_heading] = []

        for line in result.split("\n"):
            line = line.strip()

            if line.startswith("ATS SCORE:"):
                continue

            if line == "* PROFESSIONAL SUMMARY":
                continue

            line = line.strip()

            if line.endswith(":"):

                current_heading = line.replace(":", "")

                sections[current_heading] = []

            else:

                if line:

                    sections[current_heading].append(line)
        

        global latest_resume_result

        latest_resume_result = result
        timestamp = datetime.now().strftime(
    "%d %b %Y | %I:%M %p"
)


        ats_score = 0
        for line in result.split("\n"):
            if "ATS SCORE:" in line:
                try:
                    ats_score = int(
                        line.split(":")[1]
                        .split("/")[0]
                        .strip()
                   )
                    
                    
                except:

                    ats_score = 0

                break
        if ats_score >= 9:
            grade = "A+"

        elif ats_score >= 8:

            grade = "A"

        elif ats_score >= 7:

            grade = "B+"

        elif ats_score >= 6:

            grade = "B"

        elif ats_score >= 5:

            grade = "C"

        else:
            grade = "Needs Work"

        
    
        

    except Exception as e:
        ats_score = 0

        grade = "N/A"


        error_text = str(e)

        if "RESOURCE_EXHAUSTED" in error_text:

            result = """
🚫 Gemini API quota exceeded.

Please wait a minute and try again.

Thank you for using EnggBuddy 🚀
"""

        elif "API_KEY_INVALID" in error_text:
            result = """
🔑 Invalid Gemini API Key.

Please check your API key.
"""

        else:
            result = f"""
⚠️ Gemini Error:
{str(e)}
"""
    return render_template(
    "result.html",
    result=result,
    ats_score=ats_score,
    grade=grade,
    timestamp=timestamp,
    sections=sections
)
# ================= AI INTERVIEW GENERATOR =================

@app.route("/interview")
def interview():

    return render_template(
        "interview_generator.html"
    )

import json

@app.route("/generate_interview", methods=["POST"])
def generate_interview():

    topic = request.form["topic"]

    difficulty = request.form["difficulty"]

    question_type = request.form["question_type"]

    if question_type == "mcq":

        prompt = f"""
Return ONLY valid JSON.

Do not add explanations outside JSON.
Do not use markdown.
Do not use ```json.

Format:

[
  {{
    "question":"...",
    "options":["A","B","C","D"],
    "answer":"...",
    "explanation":"..."
  }}
]

Topic: {topic}
Difficulty: {difficulty}
"""

        try:


            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            raw_text = response.text

            raw_text = raw_text.replace("```json", "")
            raw_text = raw_text.replace("```", "")
            raw_text = raw_text.strip()

            mcqs = json.loads(raw_text)
            return render_template(
                "mcq_quiz.html",
                mcqs=mcqs,
                topic=topic,
                difficulty=difficulty
            )

        except Exception as e:
            return render_template(
        "interview_result.html",
        questions="""
🚫 Gemini API quota exceeded.

Please wait a minute and try again.

Or use a new API key.
""",
        topic=topic,
        difficulty=difficulty,
        question_type=question_type
    )
    else:
        prompt = f"""
You are a senior software engineering interviewer.

Generate EXACTLY 20 interview questions.

Topic:
{topic}

Difficulty:
{difficulty}

Question Type:
{question_type}

IMPORTANT:

Each question MUST be separate.

Return EXACTLY in this format:

CATEGORY: Technical Knowledge

QUESTION:
What is Flask?

ANSWER:
Flask is a lightweight Python web framework used for building web applications.

---

categories = [
    ("Technical Knowledge", 3),
    ("Problem Solving", 3),
    ("Scenario Based", 3),
    ("Project Discussion", 3),
    ("Debugging", 2),
    ("Best Practices", 2),
    ("Real World Application", 2),
    ("Behavioral", 2)
]

IMPORTANT:
Generate only 3 Technical Knowledge questions.

Technical Knowledge questions should test concepts.

Problem Solving questions should present a problem and ask for a solution.

Scenario Based questions should describe a real workplace situation.

Project Discussion questions should ask about projects built using the topic.

Debugging questions should involve finding and fixing errors.

Best Practices questions should focus on industry standards.

Real World Application questions should ask how the technology is used in production.

Behavioral questions should evaluate teamwork, learning, communication, and ownership.

Do NOT ask definition-based questions outside Technical Knowledge.

Generate 20 separate blocks.

Never combine multiple questions into one block.

Every QUESTION must contain only ONE question.

Every ANSWER must be 4-6 lines.

 

Do not use markdown.
Do not use bullet points.
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        questions = response.text
        print("\n\n========== GEMINI OUTPUT ==========\n")
        print(questions)
        print("\n===================================\n")

        cards = []

        blocks = questions.split("---")
        print("BLOCKS FOUND:", len(blocks))

        for block in blocks:

            category = ""
            question = ""
            answer = ""

            lines = block.strip().split("\n")

            mode = ""

            for line in lines:

                line = line.strip()

                if line.startswith("CATEGORY:"):

                    category = line.replace(
                        "CATEGORY:",
                        ""
                    ).strip()

                elif line == "QUESTION:":

                    mode = "question"

                elif line == "ANSWER:":

                    mode = "answer"

                else:

                    if mode == "question":

                        question += line + " "

                    elif mode == "answer":

                        answer += line + " "

            if question:

                cards.append({

                    "category": category,

                    "question": question.strip(),

                    "answer": answer.strip()

                })
                print("Cards generated:", len(cards))

        return render_template(
            "interview_result.html",
            cards=cards,
            topic=topic,
            difficulty=difficulty,
            question_type=question_type
        )

    except Exception as e:

    return render_template(
        "interview_result.html",
        cards=[],
        topic=topic,
        difficulty=difficulty,
        question_type=question_type,
        error=str(e)
    )


@app.route("/download_report")
def download_report():

    global latest_resume_result

    if latest_resume_result == "":

        return "No report available"

    file_data = BytesIO()

    file_data.write(
        latest_resume_result.encode("utf-8")
    )

    file_data.seek(0)

    return send_file(
        file_data,
        as_attachment=True,
        download_name="EnggBuddy_Report.txt",
        mimetype="text/plain"
    )

# ================= RUN APP =================

if __name__ == "__main__":

    app.run(debug=True)
