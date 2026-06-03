import os
import sys
import argparse
import base64
import io
import json
import time
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont

# 1. Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")

# Fail fast if the API key is missing
if not API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable not found.")
    print("Please set it before running the script. For example:")
    print("  Linux/macOS: export GEMINI_API_KEY='your_api_key'")
    print("  Windows CMD: set GEMINI_API_KEY='your_api_key'")
    sys.exit(1)

MODEL = "gemini-2.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

def load_font(target_size):
    # Standard font paths for Android, Windows, macOS, and Linux
    font_paths = [
        "/system/fonts/Roboto-Regular.ttf",               # Android
        "/system/fonts/DroidSans.ttf",                    # Android
        "/system/fonts/NotoSans-Regular.ttf",             # Android
        "C:/Windows/Fonts/arial.ttf",                     # Windows
        "/Library/Fonts/Arial.ttf",                       # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Linux
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=target_size)
            except IOError:
                continue
    return ImageFont.load_default()

def get_api_annotations(img_chunk, section_name):
    buffer = io.BytesIO()
    img_chunk.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    prompt = (
        "You are an expert math grader. Analyze EVERY SINGLE line of this math image snippet from top to bottom. "
        "If an equation is visibly sliced in half by the top or bottom edge of the image, IGNORE IT. "
        "Return ONLY a raw JSON array of objects. Keys: "
        "'is_correct' (boolean), "
        "'feedback' (string, maximum 8 words if wrong, empty if correct), "
        "'box_2d' (array of 4 integers: [ymin, xmin, ymax, xmax] normalized to 1000)."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}, 
                    {"inlineData": {"mimeType": "image/jpeg", "data": base64_image}}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    for attempt in range(3):
        try:
            response = requests.post(URL, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                try:
                    data = json.loads(result_text)
                    if isinstance(data, list) and len(data) > 0:
                        return data 
                except json.JSONDecodeError:
                    print(f"[{section_name}] Failed to parse JSON on attempt {attempt + 1}.")
                
            print(f"[{section_name}] Attempt {attempt + 1} failed or returned empty. Retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"[{section_name}] Error on attempt {attempt + 1}: {e}")
            time.sleep(2)
            
    print(f"WARNING: Could not grade {section_name} after 3 attempts.")
    return []

def grade_and_draw_full_paper(image_path, output_path):
    if not os.path.exists(image_path):
        print(f"Error: File not found at {image_path}")
        return

    print("Loading original image...")
    original_img = Image.open(image_path).convert("RGB")
    width, height = original_img.size
    draw = ImageDraw.Draw(original_img)
    
    font = load_font(int(height * 0.018))
    grade_font = load_font(int(height * 0.06))

    occupied_rects = []

    def is_overlapping(new_rect):
        for occ in occupied_rects:
            if not (new_rect[2] < occ[0] or new_rect[0] > occ[2] or new_rect[3] < occ[1] or new_rect[1] > occ[3]):
                return True
        return False

    midpoint = height // 2
    overlap = int(height * 0.05) 
    chunks = [
        {"box": (0, 0, width, midpoint + overlap), "y_offset": 0, "name": "Top Half"},
        {"box": (0, midpoint - overlap, width, height), "y_offset": midpoint - overlap, "name": "Bottom Half"}
    ]

    total_steps = 0
    correct_steps = 0

    for chunk in chunks:
        print(f"Processing {chunk['name']}...")
        crop_box = chunk["box"]
        y_offset = chunk["y_offset"]
        
        cropped_img = original_img.crop(crop_box)
        api_img = cropped_img.copy()
        api_img.thumbnail((1024, 1024))
        
        chunk_width, chunk_height = cropped_img.size
        grading_data = get_api_annotations(api_img, chunk["name"])

        # PASS 1: Map all equation zones
        for step in grading_data:
            box = step.get("box_2d", [0, 0, 0, 0])
            top = int((box[0] / 1000.0) * chunk_height) + y_offset
            left = int((box[1] / 1000.0) * chunk_width)
            bottom = int((box[2] / 1000.0) * chunk_height) + y_offset
            right = int((box[3] / 1000.0) * chunk_width)
            occupied_rects.append([left, top, right, bottom])

        # PASS 2: Draw marks and text
        for step in grading_data:
            total_steps += 1
            box = step.get("box_2d", [0, 0, 0, 0])
            
            top = int((box[0] / 1000.0) * chunk_height) + y_offset
            left = int((box[1] / 1000.0) * chunk_width)
            bottom = int((box[2] / 1000.0) * chunk_height) + y_offset
            right = int((box[3] / 1000.0) * chunk_width)

            is_correct = step.get("is_correct", True)
            feedback = step.get("feedback", "")

            if is_correct:
                correct_steps += 1
                chk_x = right + 20
                if chk_x + 50 > width:
                    chk_x = max(10, left - 60)
                chk_y = top + (bottom - top) // 2
                draw.line([(chk_x, chk_y), (chk_x + 15, chk_y + 15), (chk_x + 40, chk_y - 20)], fill="green", width=6)
            else:
                draw.rectangle([left, top, right, bottom], outline="red", width=6)
                
                x_x = right + 20
                if x_x + 50 > width:
                    x_x = max(10, left - 60)
                x_y = top
                draw.line([(x_x, x_y), (x_x + 40, x_y + 40)], fill="red", width=6)
                draw.line([(x_x + 40, x_y), (x_x, x_y + 40)], fill="red", width=6)
                
                char_width_estimate = int(width * 0.015) 
                max_chars = max(20, int((width - left - 40) / char_width_estimate))
                wrapped_feedback = "\n".join(textwrap.wrap(feedback, width=max_chars))
                
                try:
                    bbox = draw.textbbox((0, 0), wrapped_feedback, font=font)
                    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    text_w, text_h = draw.textsize(wrapped_feedback, font=font)
                
                text_y = max(10, top - text_h - 10)
                text_rect = [left, text_y, left + text_w, text_y + text_h]
                
                if is_overlapping(text_rect):
                    text_y = bottom + 10
                    text_rect = [left, text_y, left + text_w, text_y + text_h]
                
                attempts = 0
                while is_overlapping(text_rect) and attempts < 20:
                    text_y += 15 
                    text_rect = [left, text_y, left + text_w, text_y + text_h]
                    attempts += 1
                
                occupied_rects.append(text_rect)
                draw.text((left, text_y), wrapped_feedback, fill="red", font=font)

    print("Calculating final grade and finding safe space on page...")
    if total_steps > 0:
        raw_score = (correct_steps / total_steps) * 20
        score_20 = round(raw_score * 2) / 2
        
        grade_text = f"{int(score_20)} / 20" if score_20.is_integer() else f"{score_20} / 20"

        try:
            bbox = draw.textbbox((0, 0), grade_text, font=grade_font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(grade_text, font=grade_font)

        circle_padding = int(width * 0.05)
        stamp_w = text_w + (circle_padding * 2)
        stamp_h = text_h + (circle_padding * 2)

        found_spot = False
        stamp_x_center = int(width * 0.85) 
        stamp_y_center = int(height * 0.10)

        step_y = int(height * 0.03)
        step_x = int(width * 0.05)
        padding_margin = int(width * 0.02)

        for y in range(padding_margin, height - stamp_h, step_y):
            for x in range(width - stamp_w - padding_margin, padding_margin, -step_x):
                test_rect = [x, y, x + stamp_w, y + stamp_h]
                if not is_overlapping(test_rect):
                    stamp_x_center = x + (stamp_w // 2)
                    stamp_y_center = y + (stamp_h // 2)
                    found_spot = True
                    break
            if found_spot:
                break

        draw.ellipse(
            [stamp_x_center - stamp_w//2, stamp_y_center - stamp_h//2, 
             stamp_x_center + stamp_w//2, stamp_y_center + stamp_h//2], 
            outline="red", width=8
        )
        draw.text((stamp_x_center - text_w//2, stamp_y_center - text_h//2), grade_text, fill="red", font=grade_font)

    original_img.save(output_path)
    print(f"Success! Fully graded image saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Math Grader using Gemini Vision")
    parser.add_argument("-i", "--input", required=True, help="Path to the input image")
    parser.add_argument("-o", "--output", required=True, help="Path to save the graded image")
    
    args = parser.parse_args()
    
    grade_and_draw_full_paper(args.input, args.output)
    sys.exit(0)
