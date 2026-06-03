```markdown
# Gemini Math Grader 📝🤖

An automated AI teaching assistant that uses the **Gemini 2.5 Flash API** to visually inspect, grade, and annotate handwritten math assignments directly on the image.

This script acts like a virtual red pen. It analyzes a photo of a math paper, evaluates each step of the equations for accuracy, and draws feedback exactly where it belongs. It adds green checkmarks for correct steps, red bounding boxes with constructive feedback for errors, and stamps a final calculated grade on the page—all while smartly avoiding drawing over the student's original handwriting.

---

## ✨ Features

* **Multimodal AI Grading:** Leverages Gemini 2.5 Flash's advanced vision capabilities to read and understand handwritten math equations.
* **Spatial Annotation:** Extracts `box_2d` coordinates from the API response to map feedback precisely to the corresponding equations on the page.
* **Smart Overlap Detection:** Uses a custom grid-search algorithm to find blank spaces on the paper, ensuring that the final grade stamp and text feedback never cover up the student's work.
* **Intelligent Image Processing:** Automatically splits tall/long images into overlapping halves before sending them to the API. This maintains high resolution, prevents AI hallucinations, and ensures no details are lost.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.7** or higher
* A **Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/))

---

## 📦 Installation

**1. Clone the repository:**
```bash
git clone [https://github.com/YOUR_USERNAME/gemini-math-grader.git](https://github.com/YOUR_USERNAME/gemini-math-grader.git)
cd gemini-math-grader

```
**2. Install the required dependencies:**
```bash
pip install -r requirements.txt

```
**3. Set your API Key:**
The script requires your Gemini API key to be stored securely as an environment variable named GEMINI_API_KEY.
 * **Linux / macOS:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   
   ```
 * **Windows (Command Prompt):**
   ```cmd
   set GEMINI_API_KEY="your_api_key_here"
   
   ```
 * **Windows (PowerShell):**
   ```powershell
   $env:GEMINI_API_KEY="your_api_key_here"
   
   ```
## 🚀 Usage
Run the script from your terminal. You must provide the input image path and the desired output image path using the -i and -o flags.
```bash
python grader.py -i homework.jpg -o graded_homework.jpg

```
**Arguments:**
 * -i or --input: Path to the original photo of the homework.
 * -o or --output: Path where the graded, annotated image will be saved.
## 🧠 How it Works Under the Hood
 1. **Splitting:** The script slices the original image horizontally into a "Top Half" and "Bottom Half" (with slight overlap) to maintain maximum detail for the vision model.
 2. **Prompting:** It sends the chunks to Gemini 2.5 Flash with a strict prompt, forcing the AI to return a validated JSON array containing is_correct (boolean), feedback (short string), and box_2d (normalized coordinates).
 3. **Drawing (Pass 1 & 2):** Using the Pillow library, the script first maps out where all the equations are. Then, it draws thick green checkmarks next to correct steps, and red outlines with wrapped text feedback near incorrect steps.
 4. **Stamping:** The script tallies the correct steps to calculate a score out of 20. It then scans the image using a grid-search algorithm to find the closest un-annotated area (usually the top right) to draw a red circular stamp with the final grade.
## 📄 License
This project is licensed under the MIT License. Feel free to use, modify, and distribute it as you see fit!
```

```
