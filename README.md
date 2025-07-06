# CAREER_GUIDANCE_CHATBOT
Internship with Cynaris Solutions
#  Career Guidance Chatbot for 10th Grade Students

This is a smart, interactive chatbot designed to help 10th grade students choose the most suitable career path and stream based on their personal preferences, skills, and interests. It uses **Python (Flask)** for backend logic, a **Gemma:2B language model (via Ollama)** for summaries, and a clean **HTML/CSS UI** with no JavaScript.

![UI Screenshot](./screenshots/preview.png)

---

##  Features

-  **25-Question Skill Assessment Quiz**
-  **Collects Student Name and Preferred Career Field**
-  **Gemma-2B Model via Ollama for Summary & Personality Output**
-  **Chat-Like Experience With Button-Based Input (No Typing Required)**
-  **Skills Scored Across 5 Key Metrics:**
  - Analytical Thinking
  - Communication Skills
  - Leadership & Initiative
  - Adaptability & Resilience
  - Creative & Practical Thinking
-  **Top 3 Career Suggestions Based on % Match**
-  **Suggested Academic Stream & Personality Type**
-  **Generates Downloadable PDF Report**

---

##  Folder Structure
├── app.py # Flask backend
├── templates/
│ └── chat.html # Chatbot UI (Jinja2 + HTML)
├── static/
│ └── chat.css # Stylesheet

## 🛠️ Installation & Running

1. Install Dependencies 
pip install -r requirements.txt

2. Run Gemma Locally with Ollama
   ollama run gemma:2b
3.  Run the Flask Server
   cd "file location"
   python app.py

# Output:
<img width="1919" height="1014" alt="Image" src="https://github.com/user-attachments/assets/5d97e62a-89ec-4f69-b961-865136c44560" />

<img width="1914" height="1005" alt="Image" src="https://github.com/user-attachments/assets/f35ac33c-6e30-44a0-90df-559b7fee3575" />
