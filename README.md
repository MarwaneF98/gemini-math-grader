```markdown
# Gemini Math Grader 📝🤖

An automated script that uses the **Gemini 2.5 Flash API** to visually inspect, grade, and annotate handwritten math assignments. 

The script analyzes an image of a math paper, identifies each step of the equations, grades them for accuracy, and draws directly onto the image—adding green checkmarks for correct steps, red boxes with feedback for errors, and a final stamped grade out of 20 in the closest available blank space.

## ✨ Features
* **Vision-Based Grading:** Uses Gemini 2.5 Flash's multimodal capabilities to read handwritten math.
* **Spatial Annotation:** Extracts `box_2d` coordinates from the API to map feedback exactly where the equation appears on the page.
* **Smart Overlap Detection:** Uses a grid-search algorithm to find empty spaces on the paper so text and grade stamps don't cover up the student's original work.
* **Large Image Handling:** Splits long images in half to ensure the API catches every detail without hallucinating or losing context.

## 🛠️ Prerequisites
* Python 3.7+
* A Google Gemini API Key

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/gemini-math-grader.git](https://github.com/YOUR_USERNAME/gemini-math-grader.git)
   cd gemini-math-grader

```
 2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   
   ```
 3. **Set your API Key:**
   The script requires your API key to be set as an environment variable named GEMINI_API_KEY.
   * **Linux/macOS:** export GEMINI_API_KEY="your_api_key_here"
   * **Windows CMD:** set GEMINI_API_KEY="your_api_key_here"
   * **Windows PowerShell:** $env:GEMINI_API_KEY="your_api_key_here"
## 🚀 Usage
Run the script from your terminal, passing the input image and your desired output filename using the -i and -o flags:
```bash
python grader.py -i input_homework.jpg -o graded_homework.jpg

```
## 🧠 How it Works
 1. **Splitting:** The script slices the image horizontally into a top and bottom chunk to maintain high resolution for the AI.
 2. **Prompting:** It asks Gemini to act as a strict math grader and return a strict JSON array containing is_correct, feedback, and box_2d coordinates.
 3. **Drawing:** Using Pillow, the script iterates through the JSON. Checkmarks are drawn next to correct bounding boxes. Incorrect boxes are outlined in red with wrapped text feedback.
 4. **Stamping:** The script calculates the final score out of 20 and runs a spatial grid-search to find an un-annotated area on the paper to "stamp" the final grade.
```

```
### 5. `LICENSE` (Optional but Recommended)
If you want others to be able to use and learn from your code freely, it's standard to include an MIT License. Create a file simply named `LICENSE` (no extension) and paste this, changing the Year and Your Name:

```text
MIT License

Copyright (c) 2026 [Your Name/Username]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.