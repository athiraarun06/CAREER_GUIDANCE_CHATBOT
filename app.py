from flask import Flask, render_template, request, session, url_for
import requests, os, uuid, textwrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "careerbot-secret"

# ───────────────────── Static Data ─────────────────────
CAREER_FIELDS = [
    "Medical Field", "Engineering Field", "Software/IT Field",
    "Business & Entrepreneurship", "Creative Arts & Design", "Teaching & Academia",
    "Law & Civil Services", "Government/Defense Services", "Media & Communication",
    "Vocational Trades", "Finance & Accounting", "Social Work & Psychology"
]
ENGLISH_LEVELS = ["Excellent", "Good", "Average", "Poor"]


# [Analytical, Communication, Leadership, Adaptability, Creativity]
FIELD_MATRIX = [
    [5,4,3,5,2], [5,3,3,4,3], [5,3,3,4,4], [4,5,5,4,4],
    [2,4,3,5,5], [4,5,4,4,3], [5,5,4,4,2], [5,3,4,5,2],
    [3,5,4,5,4], [4,3,2,5,5], [5,3,3,4,2], [4,5,4,5,3]
]

# 25 scenario questions (Q, [options], skill_idx)
QUESTIONS = [
    # Analytical (0)
    ("When faced with a math problem you don’t understand, what do you do first?",
     ["Break it into smaller parts and find logic.",
      "Find a similar solved example.",
      "Ask a friend directly.",
      "Skip it for later."], 0),
    ("You are given a puzzle during a competition. How do you approach it?",
     ["Test different strategies.",
      "Try one method until it works.",
      "Guess if it looks complex.",
      "Ignore it to save time."], 0),
    ("You notice a pattern in your exam scores. What would you do with this insight?",
     ["Analyze weak areas and plan.",
      "Focus a bit more on weak topics.",
      "Study equally for all.",
      "Do nothing special."], 0),
    ("A friend asks you for help solving a problem. What’s your process?",
     ["Explain step‑by‑step.",
      "Give the answer only.",
      "Ask them to try first.",
      "Say you’re not sure."], 0),
    ("You’re assigned to research a topic for class. How do you begin?",
     ["Gather multiple sources and outline.",
      "Use first search results.",
      "Ask classmates.",
      "Wait till last minute."], 0),

    # Communication (1)
    ("You’re in a group project and your idea isn’t being understood. What do you do?",
     ["Use an example/visual.",
      "Repeat more clearly.",
      "Let them move on.",
      "Stay silent."], 1),
    ("How do you explain your opinions in a debate?",
     ["Use facts & examples.",
      "State briefly.",
      "Share feelings only.",
      "Avoid debates."], 1),
    ("You need help with homework from your teacher. How do you ask?",
     ["Ask a specific question.",
      "Say you didn’t understand.",
      "Ask for the answer.",
      "Don’t ask."], 1),
    ("When writing an essay, what is your focus?",
     ["Structure & creativity.",
      "Stay on topic.",
      "Reach word count.",
      "Finish quickly."], 1),
    ("You disagree with someone in class. How do you express it?",
     ["Share respectfully.",
      "Explain why you differ.",
      "Keep quiet.",
      "Argue loudly."], 1),

    # Leadership (2)
    ("No one leads in a team. What do you do?",
     ["Take the lead.",
      "Suggest actions.",
      "Wait for someone else.",
      "Just follow."], 2),
    ("You have an idea for a school event but no one mentions it. What do you do?",
     ["Pitch it confidently.",
      "Mention quietly.",
      "Wait to see if others mention.",
      "Keep it to yourself."], 2),
    ("A group project isn’t moving. Next step?",
     ["Call a discussion & solve it.",
      "Do your part more actively.",
      "Wait for others.",
      "Ignore it."], 2),
    ("Lead or follow in an activity — what do you choose?",
     ["Lead with ideas.",
      "Follow but engage.",
      "Join later.",
      "Avoid involvement."], 2),
    ("You see someone struggling with a task. What do you do?",
     ["Offer help & guide.",
      "Ask if they need help.",
      "Inform the teacher.",
      "Do nothing."], 2),

    # Adaptability (3)
    ("Schedule suddenly changes. How do you react?",
     ["Adjust quickly.",
      "Follow quietly.",
      "Complain but comply.",
      "Skip class."], 3),
    ("You fail a test you studied for. Next?",
     ["Seek feedback & improve.",
      "Study harder.",
      "Feel down & study less.",
      "Ignore it."], 3),
    ("Given a task you’ve never done. Approach?",
     ["Try & ask guidance.",
      "Try & learn mistakes.",
      "Rely on others.",
      "Avoid it."], 3),
    ("Friend cancels plans last minute. What do you do?",
     ["Do something else.",
      "Say okay but sad.",
      "Complain to others.",
      "Get angry."], 3),
    ("Teacher switches partner mid‑project. How do you handle?",
     ["Coordinate quickly.",
      "Accept & try best.",
      "Feel uncomfortable.",
      "Ask to drop."], 3),

    # Creative (4)
    ("Design a poster: first step?",
     ["Sketch concept ideas.",
      "Look online for inspiration.",
      "Copy an old design.",
      "Let others do it."], 4),
    ("Make a boring topic interesting. How?",
     ["Use visuals/stories.",
      "Prepare concise notes.",
      "Read content aloud.",
      "Avoid presenting."], 4),
    ("Leftover materials for art project. You…",
     ["Create something unique.",
      "Use what fits.",
      "Do minimum work.",
      "Complain & delay."], 4),
    ("Think of a new way to do a daily task. Response?",
     ["Brainstorm & test ideas.",
      "Ask others suggestions.",
      "Do it the usual way.",
      "Say unnecessary."], 4),
    ("Students don’t use school app. You suggest?",
     ["Recommend improvements.",
      "Share feedback.",
      "Tell friends only.",
      "Ignore issue."], 4)
]

QUESTION_SCORE = [4, 3, 2, 1]

# ───── helper functions ─────
def llm(prompt):
    try:
        res = requests.post("http://localhost:11434/api/generate",
                            json={"model": "gemma:2b", "prompt": prompt, "stream": False},
                            timeout=60)
        return res.json()["response"].strip()
    except Exception:
        return "(Gemma 2B offline.)"

def raw_to_level(raw):
    return 5 if raw >= 17 else 4 if raw >= 13 else 3 if raw >= 9 else 2

# ───── session reset ─────
def reset():
    session.clear()
    session.update(
        step="name", name="", field="Not selected", english="Good",
        q_idx=0, scores=[0,0,0,0,0],
        messages=[("bot", "Hi! What’s your <b>name</b>?")],
        quick_replies=[], show_footer=False
    )

# ───── Flask route ─────
@app.route("/", methods=["GET", "POST"])
def chat():
    if "step" not in session:
        reset()

    if request.method == "POST":
        msg = request.form["user_input"].strip()
        session["messages"].append(("user", msg))
        advance(msg)

    return render_template("chat.html",
                           messages=session["messages"],
                           quick_replies=session.get("quick_replies", []),
                           show_footer=session.get("show_footer", False))

# ───── dialogue engine ─────
def advance(text):
    # ensure keys
    session.setdefault("q_idx", 0); session.setdefault("scores", [0,0,0,0,0])
    step = session["step"]

    if step == "name":
        session["name"] = text
        ask(f"Nice to meet you, <b>{text}</b>! Pick a career field:",
            CAREER_FIELDS, "field"); return

    if step == "field":
        session["field"] = text
        ask("How fluent are you in English?", ENGLISH_LEVELS, "english"); return

    if step == "english":
        if text not in ENGLISH_LEVELS:
            ask("Please tap a button ↓", ENGLISH_LEVELS, stay=True); return
        session["english"] = text
        session["step"] = "quiz"
        ask_question(0); return

    if step == "quiz":
        i = session["q_idx"]
        if i >= len(QUESTIONS): finish(); return
        q, opts, skill = QUESTIONS[i]
        if text not in opts:
            ask("Choose an option ↓", opts, stay=True); return
        session["scores"][skill] += QUESTION_SCORE[opts.index(text)]
        session["q_idx"] = i + 1
        if session["q_idx"] < len(QUESTIONS):
            ask_question(session["q_idx"])
        else:
            finish(); return

    if step == "restart":
        reset()

# ───── helper ask ----------
def ask(msg, buttons, next_step=None, stay=False):
    session["messages"].append(("bot", msg))
    session["quick_replies"] = buttons
    if next_step and not stay:
        session["step"] = next_step

def ask_question(i):
    q, opts, _ = QUESTIONS[i]
    ask(f"<b>Q{i+1}.</b> {q}", opts)

# ───── personality & stream ----------
def personality(lv):
    a,c,l,ad,cr = lv
    if all(x>=4 for x in lv): return "The Achiever"
    if a==5 and (c>=4 or ad>=4): return "The Thinker"
    if c==5 and l>=4: return "The Communicator"
    if cr==5 and (l>=4 or ad>=4): return "The Visionary"
    if ad==5 and (l>=4 or c>=4): return "The Helper"
    if cr>=4 and ad>=4 and all(lv[i]<4 for i in (0,1,2)): return "The Doer"
    return "The Achiever"

def stream(lv, field):
    if lv[0] >= 4: return "Science"
    if field in ("Business & Entrepreneurship","Finance & Accounting"): return "Commerce"
    if lv[1] >= 4 or lv[4] >= 4: return "Arts/Humanities"
    return "Commerce"

# ───── PDF helper ----------
def make_pdf(name, lv, top3, subj, ptype, advice, path):
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    margin = 50
    y = h - margin

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, y, "Career Guidance Report")
    y -= 28
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, y, f"for {name}")
    y -= 32
    c.line(margin, y, w-margin, y)
    y -= 28

    def heading(txt):
        nonlocal y
        c.setFont("Helvetica-Bold", 12); c.drawString(margin, y, txt); y -= 18

    def bullets(lines):
        nonlocal y
        c.setFont("Helvetica", 11)
        for line in lines:
            c.drawString(margin+14, y, u"\u2022 " + line)
            y -= 14

    skills = ["Analytical","Communication","Leadership","Adaptability","Creativity"]
    heading("Skill Ratings")
    bullets([f"{s}: {v}/5" for s,v in zip(skills, lv)])

    heading("Top Career Matches")
    bullets([f"{f} – {p}%" for f,p in top3])

    heading("Recommended Stream")
    bullets([subj])

    heading("Personality Type")
    bullets([ptype])

    heading("Counsellor Advice")
    bullets(textwrap.wrap(advice, 88))

    y -= 10; c.line(margin, y, w-margin, y); y -= 18
    c.setFont("Helvetica-Oblique", 11)
    c.drawString(margin, y, "Wishing you a bright future! Reach out anytime for career guidance.")
    c.save()

# ───── finish ─────
def finish():
    lv = [raw_to_level(r) for r in session["scores"]]
    lv[1] = max(1, min(5, lv[1] + {"Excellent":1,"Good":0,"Average":-1,"Poor":-2}[session["english"]]))

    fits = []
    for f, req in zip(CAREER_FIELDS, FIELD_MATRIX):
        fits.append((f, int(sum(min(1, lv[j]/req[j]) for j in range(5))/5*100)))
    fits.sort(key=lambda x:-x[1]); top3 = fits[:3]

    ptype = personality(lv)
    subj  = stream(lv, session["field"])
    advice = llm(f"Summarise in 2 friendly sentences. Skills {lv}. Stream {subj}. Personality {ptype}.")

    # create PDF
    pdf_file = uuid.uuid4().hex + ".pdf"
    pdf_rel  = f"reports/{pdf_file}"
    os.makedirs(os.path.join("static", "reports"), exist_ok=True)
    make_pdf(session["name"], lv, top3, subj, ptype, advice,
             os.path.join("static", pdf_rel))

    pdf_url = url_for("static", filename=pdf_rel)
    iframe  = f'<iframe src="{pdf_url}#toolbar=0" style="width:100%;height:420px;border:1px solid #ccc;border-radius:8px;"></iframe>'
    dl_link = f'<a href="{pdf_url}" target="_blank" download>⬇ Download PDF</a>'

    skills_html = "<br>".join(f"{n}: {v}/5" for n,v in zip(
        ["Analytical","Communication","Leadership","Adaptability","Creativity"], lv))
    top_html = "<br>".join(f"{f} – {p}%" for f,p in top3)
    html = (f"<b>Results</b><br>{skills_html}<br><br><b>Top Career Matches</b><br>{top_html}"
            f"<br><b>Suggested Stream:</b> {subj}<br><b>Personality:</b> {ptype}<br><br>"
            f"{advice}<br><br>{iframe}<br>{dl_link}")

    session["messages"].append(("bot", html))
    session.update(step="restart", quick_replies=["Restart"], show_footer=True)

# ───── run ─────
if __name__ == "__main__":
    app.run(debug=True)
