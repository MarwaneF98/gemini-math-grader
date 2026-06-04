# Gemini Math Grader 📝🤖
An automated AI teaching assistant that uses the **Gemini 3.5 Flash API** to visually inspect, grade, and annotate handwritten math assignments directly on the image.
This script acts like a virtual red pen. It analyzes a photo of a math paper, evaluates each step of the equations for accuracy, and draws feedback exactly where it belongs. It adds green checkmarks for correct steps, red bounding boxes with constructive feedback for errors, and stamps a final calculated grade on the page—all while smartly dodging the student's original handwriting and preventing annotation collisions.
## ✨ Features
 * **Multimodal AI Grading:** Leverages Gemini 3.5 Flash's advanced vision capabilities to read and evaluate handwritten math equations, whiteboards, and digital screens.
 * **Ultra-Fast Single Pass:** Processes the entire image in one optimized API call, bringing grading time down to just a few seconds.
 * **Teacher's Margin Alignment:** Automatically aligns checkmarks and 'X' marks into a neat, professional column down the right side of the page.
 * **3-Phase Rendering Engine:** Eliminates visual traffic jams. It locks in the math boxes and grade stamp *first*, forcing detailed feedback notes to route around them into safe, empty spaces.
 * **Semi-Transparent Overlays:** Uses beautiful, semi-opaque backgrounds for notes and stamps, ensuring the student's original math is always readable underneath.
## 🛠️ Prerequisites
Before you begin, ensure you have the following installed:
 * **Python 3.7+**
 * A **Google Gemini API Key** (You can get one for free from Google AI Studio)
 * The Pillow library for image processing
## 📦 Installation
**1. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/gemini-math-grader.git
cd gemini-math-grader

```
**2. Install the required dependencies:**
```bash
pip install -r requirements.txt

```
*(Note: Your requirements.txt should contain requests and Pillow)*
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
python grader.py -i input_homework.jpg -o graded_homework.jpg

```
**Arguments:**
 * -i or --input: Path to the original photo of the homework.
 * -o or --output: Path where the graded, annotated image will be saved.
## 🧠 How it Works Under the Hood
 1. **Pre-Processing:** The script loads the image and corrects any hidden EXIF rotation data (common in mobile phone photos) so bounding boxes map perfectly to the visual text.
 2. **Prompting:** It sends the full image to Gemini 3.5 Flash with a strict prompt, forcing the AI to return a validated JSON array containing is_correct (boolean), feedback (short string), and box_2d (normalized coordinates). It specifically ignores signatures and plain text at the bottom.
 3. **Phase 1 & 2 (Marks & Stamp):** It maps out the equations, draws Checkmarks and Xs neatly in the right margin, and pastes an opaque "Score Stamp" in the top right corner. It registers all these areas as "Occupied".
 4. **Phase 3 (Smart Routing):** It evaluates incorrect steps and draws text feedback boxes. Using a radial search algorithm, the notes dynamically look for empty space nearby, gracefully dodging the stamp, the margin marks, and other notes!
## 📄 License
This project is licensed under the MIT License. Feel free to use, modify, and distribute it!
