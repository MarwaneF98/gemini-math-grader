# Gemini Math Grader 📝🤖

[![Live Demo](https://img.shields.io/badge/Live%20Demo-gemini--math--grader.vercel.app-success?style=for-the-badge)](https://gemini-math-grader.vercel.app/)

![Made in Morocco](https://img.shields.io/badge/Made%20in-Morocco-c1272d?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Pillow](https://img.shields.io/badge/Library-Pillow%20(PIL)-11557c?style=for-the-badge&logo=python&logoColor=white)
![HTML5](https://img.shields.io/badge/Frontend-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/Styling-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/Logic-JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E)
![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Gemini API](https://img.shields.io/badge/AI_Engine-Gemini%203.5%20Flash-8A2BE2?style=for-the-badge&logo=google&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Windows%20%7C%20Linux%20%7C%20Android%20(Termux/Pydroid)-lightgrey?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

An automated AI teaching assistant that uses the **Gemini 3.5 Flash API** to visually inspect, grade, and annotate handwritten math assignments directly on the image. 

</div>

Whether you want to use the sleek web interface directly from your browser or run the Python script locally from your terminal, this tool acts like a virtual red pen. It analyzes a photo of a math paper, evaluates each step, and draws dynamic feedback exactly where it belongs—dodging the student's original handwriting and preventing annotation collisions.

---

## ✨ Features

* **Premium Modern UI:** A sleek, fully responsive dark-mode web application featuring a modern dropzone for file uploads, rounded corners, and native mobile support.
* **Resolution-Independent Rendering:** Text scaling, visual padding, and UI elements (like the score stamp) mathematically adapt to the aspect ratio and resolution of any uploaded photo, ensuring perfect proportions whether the image is 4K or 720p.
* **Native Unicode Math Engine:** Bypasses heavy LaTeX backend dependencies by commanding the AI to output pure Unicode math symbols (x², ½, √), keeping serverless deployments lightning-fast while maintaining textbook-quality notation on the final image.
* **Instant Web Access:** No installation required. Just visit the live site, enter your own API key, and start grading.
* **Privacy-First API Key Storage:** In the web app, your Gemini API key is securely saved directly to your browser's local memory (`localStorage`). It is never stored on our servers.
* **Bilingual Interface (EN/FR):** A seamless English/French language toggle. The AI's feedback and the graded stamp translate dynamically.
* **Professor-Level Grading Logic (ECF):** Emulates a real university professor by using **Error Carried Forward (ECF)**. If a student makes a minor arithmetic mistake but their subsequent mathematical logic remains sound, they are not heavily penalized.
* **Weighted Scoring & Dynamic Colors:** Grades line-by-line using a 4-tier color system: Green Checkmarks (Flawless), Blue Checkmarks (Error Carried Forward), Purple Boxes (Minor Errors), and Crimson Red Boxes (Conceptual Errors).
* **3-Phase Rendering Engine:** Eliminates visual traffic jams. It locks in the math boxes and grade stamp *first*, forcing detailed text feedback to route around them into safe, empty spaces using a radial search algorithm.

---

## 🚀 How to Use

You can use the Math Grader in two different ways depending on your preference:

### Method 1: The Live Web App (Easiest)
You do not need to install anything or know how to code to use this tool.
1. Go to the live website: **[https://gemini-math-grader.vercel.app/](https://gemini-math-grader.vercel.app/)**
2. Enter your **Google Gemini API Key** (You can get one for free from Google AI Studio).
3. Select your language (EN/FR).
4. Upload a photo of the math homework and click "Grade Paper"!

### Method 2: Local CLI Script (`grader.py`)
If you are a developer and prefer to grade papers directly from your terminal or a mobile Python environment (like Pydroid/Termux), use the standalone script.

**1. Clone & Install:**
```bash
git clone [https://github.com/MarwaneF98/gemini-math-grader.git](https://github.com/MarwaneF98/gemini-math-grader.git)
cd gemini-math-grader
pip install -r requirements.txt

```
**2. Set your API Key Environment Variable:**
 * **Linux / macOS / Termux:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   
   ```
 * **Windows (Command Prompt):**
   ```cmd
   set GEMINI_API_KEY="your_api_key_here"
   
   ```
**3. Run the Grader:**
```bash
python grader.py -i input_homework.jpg -o graded_homework.jpg

```
## 🛠️ For Developers: Host Your Own Web App
If you want to fork this project and host your own version of the website, it is fully configured for Vercel.
 1. Create a free account on Vercel.
 2. Connect your GitHub account and import your forked repository.
 3. Vercel will automatically read the vercel.json and requirements.txt files, set up the Python environment, and deploy your frontend and backend seamlessly.
## 🧠 How it Works Under the Hood
 1. **Pre-Processing:** The script loads the image and corrects any hidden EXIF rotation data (common in mobile phone photos) so bounding boxes map perfectly to the visual text.
 2. **Prompting:** It sends the full image to Gemini with a strict prompt, forcing the AI to extract data into a perfectly formatted JSON array. It actively filters out polite conversational text to prevent JSON parsing crashes.
 3. **Phase 1 (Weighted Scoring & Stamp):** It calculates a weighted final score by evaluating every single line. Correct steps and ECF steps earn full credit, minor errors earn partial credit, and conceptual errors earn zero. It then dynamically scales and pastes an opaque "Score Stamp" in the top right corner and registers this area as "Occupied".
 4. **Phase 2 (Dynamic Math Boxes & Marks):** It maps out the individual equation lines in the right margin, drawing Green checkmarks for flawless steps, Blue checkmarks for logic recoveries (ECF), Purple boxes for minor mistakes, and Red boxes for conceptual failures.
 5. **Phase 3 (Smart Routing):** It evaluates incorrect steps and draws text feedback boxes. Using a custom radial search algorithm, the notes dynamically look for empty space nearby, gracefully dodging the stamp, the margin marks, and the original equations. Connector lines intelligently anchor to the sides of the error boxes to keep the math clear!
## 📄 License
© 2026 Marwane Farhane (❄️ Snowflake). Licensed under the MIT License. Feel free to fork, modify, and distribute it!