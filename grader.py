import os
import sys
import argparse
import base64
import io
import json
import time
import math
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps

# 1. Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")

# Fail fast if the API key is missing
if not API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable not found.")
    print("Please set it before running the script. For example:")
    print("  Linux/macOS: export GEMINI_API_KEY='your_api_key'")
    print("  Windows CMD: set GEMINI_API_KEY='your_api_key'")
    sys.exit(1)

MODEL = "gemini-3.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# --- DESIGN COLORS ---
COLOR_CORRECT = (22, 163, 74, 255)       # Green (Flawless)
COLOR_ECF = (59, 130, 246, 255)          # Blue (Error Carried Forward)
COLOR_MINOR = (147, 51, 234, 255)        # Purple (Minor Errors)
COLOR_WRONG = (220, 38, 38, 255)         # Red (Conceptual Errors)
COLOR_NOTE_BG = (255, 255, 255, 245)     

def load_font(target_size, bold=False):
    # 1. First, try to load a local font file
    local_font_path = os.path.join(os.path.dirname(__file__), "Roboto-Bold.ttf")
    if os.path.exists(local_font_path):
        try:
            return ImageFont.truetype(local_font_path, size=target_size)
        except IOError:
            pass

    # 2. Next, try standard system fonts
    font_paths = [
        "/system/fonts/Roboto-Bold.ttf" if bold else "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/NotoSans-Bold.ttf" if bold else "/system/fonts/NotoSans-Regular.ttf",
        "/system/fonts/DroidSans-Bold.ttf" if bold else "/system/fonts/DroidSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=target_size)
            except IOError:
                continue
    return ImageFont.load_default()

def get_api_annotations(img_chunk):
    buffer = io.BytesIO()
    img_chunk.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    prompt = (
        "You are an expert mathematics professor grading a paper.\n"
        "CRITICAL RULES:\n"
        "1. DO NOT grade signatures, names, dates, or plain text. ABSOLUTELY IGNORE anything at the very bottom of the page.\n"
        "2. Group the math into distinct problems. Evaluate every single horizontal line of math. Keep bounding boxes TIGHT.\n"
        "3. Grade using ERROR CARRIED FORWARD (ECF). If a student makes a mistake, but their subsequent steps are logically valid based on that mistake, mark those subsequent steps as 'error_carried_forward'.\n"
        "Return ONLY a raw JSON array of problem objects. Keys for each problem:\n"
        "- 'lines' (array of objects for each line. Keys:\n"
        "   * 'status' (string, MUST BE EXACTLY ONE OF: 'correct', 'minor_error', 'conceptual_error', 'error_carried_forward'),\n"
        "   * 'feedback' (string, max 10 words if error, empty if correct or error_carried_forward),\n"
        "   * 'box_2d' (array of 4 ints: [ymin, xmin, ymax, xmax] normalized to 1000))."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": base64_image}}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    for attempt in range(3): 
        try:
            print(f"Attempt {attempt + 1}: Sending to Gemini 3.5 Flash...", flush=True)
            response = requests.post(URL, json=payload, headers={"Content-Type": "application/json"}, timeout=50)
            if response.status_code == 200:
                result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                
                # Isolate the JSON array
                start_idx = result_text.find('[')
                end_idx = result_text.rfind(']')
                
                if start_idx != -1 and end_idx != -1:
                    clean_json_str = result_text[start_idx:end_idx+1]
                    try:
                        data = json.loads(clean_json_str)
                        if isinstance(data, list):
                            print("Success! JSON parsed correctly.", flush=True)
                            return data 
                    except json.JSONDecodeError:
                        time.sleep(2)
                else:
                    time.sleep(2)
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)
    return []

def is_overlapping(new_rect, occupied_rects, padding=15):
    nr = [new_rect[0]-padding, new_rect[1]-padding, new_rect[2]+padding, new_rect[3]+padding]
    for occ in occupied_rects:
        if not (nr[2] < occ[0] or nr[0] > occ[2] or nr[3] < occ[1] or nr[1] > occ[3]):
            return True
    return False

def find_safe_spot(cx, cy, text_w, text_h, img_w, img_h, occupied_rects, padding=30):
    step = 25 
    for radius in range(0, max(img_w, img_h), step):
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            test_x = int(cx + radius * math.cos(rad))
            test_y = int(cy + radius * math.sin(rad))
            
            rect = [test_x, test_y, test_x + text_w, test_y + text_h]
            
            if rect[0] < 10 or rect[1] < 60 or rect[2] > img_w - 10 or rect[3] > img_h - 10:
                continue
            
            if not is_overlapping(rect, occupied_rects, padding=padding):
                return rect
                
    safe_x = min(max(10, cx), img_w - text_w - 10)
    safe_y = min(max(60, cy), img_h - text_h - 10)
    return [safe_x, safe_y, safe_x + text_w, safe_y + text_h]

def draw_focus_box(draw, left, top, right, bottom, color, line_w=2):
    length = min(30, (right - left) // 4)
    thick = max(3, line_w * 2)
    thin = max(1, line_w)
    draw.rectangle([left, top, right, bottom], outline=color, width=thin)
    draw.line([(left, top+length), (left, top), (left+length, top)], fill=color, width=thick)
    draw.line([(right-length, top), (right, top), (right, top+length)], fill=color, width=thick)
    draw.line([(left, bottom-length), (left, bottom), (left+length, bottom)], fill=color, width=thick)
    draw.line([(right-length, bottom), (right, bottom), (right, bottom-length)], fill=color, width=thick)

def draw_stamp(img_w, img_h, score_text):
    # Scale font based on the smallest dimension to prevent massive stamps on tall photos
    base_font_size = int(min(img_w, img_h) * 0.05)
    stamp_font = load_font(base_font_size, bold=True)
    label_font = load_font(int(base_font_size * 0.45), bold=True)
    
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    try:
        bbox = temp_draw.textbbox((0, 0), score_text, font=stamp_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = temp_draw.textsize(score_text, font=stamp_font)

    # DYNAMIC CIRCLE SCALING: Force the circle to be 1.6x larger than the text itself
    stamp_size = int(max(text_w, text_h) * 1.6)
    stamp = Image.new("RGBA", (stamp_size, stamp_size), (255, 255, 255, 0))
    s_draw = ImageDraw.Draw(stamp)
    
    out_m = int(stamp_size * 0.02)
    in_m = int(stamp_size * 0.09)
    out_w = max(2, int(stamp_size * 0.025))
    in_w = max(1, int(stamp_size * 0.01))

    s_draw.ellipse([out_m, out_m, stamp_size-out_m, stamp_size-out_m], fill=(255, 255, 255, 255), outline=COLOR_WRONG, width=out_w)
    s_draw.ellipse([in_m, in_m, stamp_size-in_m, stamp_size-in_m], outline=COLOR_WRONG, width=in_w)
    
    # DYNAMIC TEXT PLACEMENT (Perfectly centered proportionally)
    s_draw.text((stamp_size//2, int(stamp_size * 0.32)), "SCORE", fill=COLOR_WRONG, font=label_font, anchor="mm")
    s_draw.text((stamp_size//2, int(stamp_size * 0.65)), score_text, fill=COLOR_WRONG, font=stamp_font, anchor="mm")
    
    return stamp.rotate(-15, expand=True, resample=Image.BICUBIC)

def grade_and_draw_full_paper(image_path, output_path):
    if not os.path.exists(image_path):
        print(f"Error: File not found at {image_path}")
        return

    print("Loading original image...")
    original_img = Image.open(image_path)
    original_img = ImageOps.exif_transpose(original_img).convert("RGBA")
    width, height = original_img.size
    
    overlay = Image.new("RGBA", original_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # DYNAMIC GLOBAL SCALING FACTORS
    font_size = int(height * 0.016)
    font = load_font(font_size, bold=True)
    line_w = max(2, int(height * 0.003))
    mark_scale = max(2, int(height * 0.006))
    
    occupied_rects = []
    
    print("Analyzing the entire page in one pass...")
    api_img = original_img.copy().convert("RGB")
    api_img.thumbnail((1536, 1536))
    
    grading_results = get_api_annotations(api_img)

    if not grading_results:
        print("ERROR: AI failed to parse the math or API limit reached. Check connection and key.")
        sys.exit(1)

    valid_results = []
    total_possible_points = 0
    earned_points = 0

    for problem in grading_results:
        if not isinstance(problem, dict):
            continue

        for step in problem.get("lines", []):
            box = step.get("box_2d", [0, 0, 0, 0])
            top = int((box[0] / 1000.0) * height)
            left = int((box[1] / 1000.0) * width)
            bottom = int((box[2] / 1000.0) * height)
            right = int((box[3] / 1000.0) * width)
            
            # Hard filter to protect the bottom signature area
            if top > height * 0.85:
                continue
                
            step["global_box"] = [left, top, right, bottom]
            valid_results.append(step)

            # PROFESSOR SCORING LOGIC
            status = step.get("status", "correct")
            total_possible_points += 2
            
            if status == "correct" or status == "error_carried_forward":
                earned_points += 2
            elif status == "minor_error":
                earned_points += 1

    # ==========================================
    # PHASE 1: Stamp Reservation
    # ==========================================
    stamp_x, stamp_y = 0, 0
    stamp_rect = [0, 0, 0, 0]
    stamp_img = None
    
    if total_possible_points > 0:
        raw_score = (earned_points / total_possible_points) * 20
        score_20 = round(raw_score * 2) / 2
        grade_text = f"{int(score_20)}/20" if score_20.is_integer() else f"{score_20}/20"

        stamp_img = draw_stamp(width, height, grade_text)
        s_w, s_h = stamp_img.size

        stamp_x = width - s_w - int(width * 0.03)
        stamp_y = int(height * 0.03)
        stamp_rect = [stamp_x, stamp_y, stamp_x + s_w, stamp_y + s_h]
        occupied_rects.append(stamp_rect) 

    # ==========================================
    # PHASE 2: Draw Math Boxes and Margin Marks
    # ==========================================
    for step in valid_results:
        left, top, right, bottom = step["global_box"]
        status = step.get("status", "correct")

        box_cy = top + (bottom - top) // 2
        
        # DYNAMIC MARGIN MARK POSITIONING
        mark_x = width - int(width * 0.06) 
        mark_y = box_cy

        if stamp_img and (stamp_rect[1] - (mark_scale*5) <= mark_y <= stamp_rect[3] + (mark_scale*5)):
            mark_x = stamp_rect[0] - int(width * 0.04)

        temp_mark_rect = [mark_x - (mark_scale*3), mark_y - (mark_scale*3), mark_x + (mark_scale*5), mark_y + (mark_scale*5)]
        occupied_rects.append(temp_mark_rect)

        draw_right = min(right, mark_x - int(width * 0.03))
        step["draw_right"] = draw_right 
        
        occupied_rects.append([left, top, draw_right, bottom])

        # DYNAMIC CHECKMARKS & X MARKS
        if status == "correct":
            points = [(mark_x, mark_y), (mark_x + int(mark_scale*1.5), mark_y + int(mark_scale*1.5)), (mark_x + int(mark_scale*5), mark_y - int(mark_scale*3))]
            draw.line(points, fill=COLOR_CORRECT, width=line_w, joint="curve")
        elif status == "error_carried_forward":
            points = [(mark_x, mark_y), (mark_x + int(mark_scale*1.5), mark_y + int(mark_scale*1.5)), (mark_x + int(mark_scale*5), mark_y - int(mark_scale*3))]
            draw.line(points, fill=COLOR_ECF, width=line_w, joint="curve")
        else:
            error_color = COLOR_MINOR if status == "minor_error" else COLOR_WRONG
            draw_focus_box(draw, left, top, draw_right, bottom, error_color, line_w=max(1, line_w-1))
            draw.line([(mark_x, mark_y - int(mark_scale*2)), (mark_x + int(mark_scale*4), mark_y + int(mark_scale*2))], fill=error_color, width=line_w)
            draw.line([(mark_x + int(mark_scale*4), mark_y - int(mark_scale*2)), (mark_x, mark_y + int(mark_scale*2))], fill=error_color, width=line_w)

    # ==========================================
    # PHASE 3: Draw the Feedback Notes
    # ==========================================
    for step in valid_results:
        status = step.get("status", "correct")
        feedback = step.get("feedback", "")
        
        if status in ["correct", "error_carried_forward"] or not feedback:
            continue

        left, top, right, bottom = step["global_box"]
        draw_right = step["draw_right"]
        box_cx = left + (draw_right - left) // 2
        box_cy = top + (bottom - top) // 2

        error_color = COLOR_MINOR if status == "minor_error" else COLOR_WRONG

        char_width_estimate = int(width * 0.015) 
        max_chars = max(15, int((width * 0.25) / char_width_estimate))
        wrapped_feedback = "\n".join(textwrap.wrap(feedback, width=max_chars, break_long_words=False))
        
        try:
            bbox = draw.textbbox((0, 0), wrapped_feedback, font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(wrapped_feedback, font=font)
        
        # DYNAMIC BOX PADDING (Scales with font size)
        pad_x = int(font_size * 0.8)
        pad_y = int(font_size * 0.6)
        
        text_w += (pad_x * 2) 
        text_h += (pad_y * 2) 

        start_search_x = draw_right + 10
        start_search_y = top - pad_y
        
        if (draw_right - left > width * 0.6) or (start_search_x + text_w > width - 10):
            start_search_x = max(10, box_cx - (text_w // 2))
            start_search_y = top - text_h - (pad_y * 2)
        
        dynamic_search_padding = int(width * 0.02)
        note_rect = find_safe_spot(start_search_x, start_search_y, text_w, text_h, width, height, occupied_rects, padding=dynamic_search_padding)
        occupied_rects.append(note_rect) 
        
        note_cx = note_rect[0] + text_w // 2
        note_cy = note_rect[1] + text_h // 2
        
        if note_cx > box_cx:      
            line_start = (draw_right, box_cy)
        else:                           
            line_start = (left, box_cy)

        draw.line([line_start, (note_cx, note_cy)], fill=error_color, width=max(2, line_w - 1))
        draw.rectangle(note_rect, fill=COLOR_NOTE_BG, outline=error_color, width=max(1, line_w - 2))
        
        # DYNAMIC TEXT CENTERING (Perfectly balanced relative to the padding)
        text_offset_y = int(pad_y * 0.5)
        draw.text((note_rect[0] + pad_x, note_rect[1] + text_offset_y), wrapped_feedback, fill=error_color, font=font)

    if stamp_img:
        overlay.paste(stamp_img, (stamp_x, stamp_y), stamp_img)

    final_img = Image.alpha_composite(original_img, overlay)
    final_img.convert("RGB").save(output_path)
    print(f"Success! Fully graded image saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Math Grader using Gemini Vision")
    parser.add_argument("-i", "--input", required=True, help="Path to the input image")
    parser.add_argument("-o", "--output", required=True, help="Path to save the graded image")
    
    args = parser.parse_args()
    
    grade_and_draw_full_paper(args.input, args.output)
    sys.exit(0)
