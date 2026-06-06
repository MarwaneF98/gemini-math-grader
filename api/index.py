import os
import io
import json
import time
import math
import base64
import requests
import textwrap
from flask import Flask, request, send_file, Response
from PIL import Image, ImageDraw, ImageFont, ImageOps

app = Flask(__name__)

# ==========================================
# ROUTE 1: SERVE THE FRONTEND HTML
# ==========================================
@app.route('/')
def serve_frontend():
    try:
        root_dir = os.path.dirname(os.path.dirname(__file__))
        index_path = os.path.join(root_dir, 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return Response(html_content, mimetype='text/html')
    except Exception as e:
        return f"CRITICAL ERROR: Could not load index.html. Ensure it is in the root folder. Details: {str(e)}", 500

# --- DESIGN COLORS ---
COLOR_CORRECT = (22, 163, 74, 255)       
COLOR_ECF = (59, 130, 246, 255)          
COLOR_MINOR = (147, 51, 234, 255)        
COLOR_WRONG = (220, 38, 38, 255)         
COLOR_NOTE_BG = (255, 255, 255, 245)     

def load_font(target_size):
    local_font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Roboto-Bold.ttf")
    if os.path.exists(local_font_path):
        try:
            return ImageFont.truetype(local_font_path, size=target_size)
        except IOError:
            pass
    return ImageFont.load_default()

def get_api_annotations(img_chunk, api_key, language_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    buffer = io.BytesIO()
    img_chunk.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    prompt = (
        "You are an expert mathematics professor grading a paper.\n"
        "CRITICAL RULES:\n"
        "1. DO NOT grade signatures, names, dates, or plain text. ABSOLUTELY IGNORE anything at the very bottom of the page.\n"
        "2. Group the math into distinct problems. Evaluate every single horizontal line of math. Keep bounding boxes TIGHT.\n"
        "3. Grade using ERROR CARRIED FORWARD (ECF). If a student makes a mistake, but their subsequent steps are logically valid based on that mistake, mark those subsequent steps as 'error_carried_forward'.\n"
        f"4. CRITICAL: Write all 'feedback' strictly in {language_name}.\n"
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
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=50)
            
            if response.status_code == 200:
                result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                
                start_idx = result_text.find('[')
                end_idx = result_text.rfind(']')
                
                if start_idx != -1 and end_idx != -1:
                    clean_json_str = result_text[start_idx:end_idx+1]
                    try:
                        data = json.loads(clean_json_str)
                        if isinstance(data, list):
                            print("Success! JSON parsed correctly.", flush=True)
                            return data 
                    except json.JSONDecodeError as e:
                        print(f"JSON Parse Error: {e}", flush=True)
                        time.sleep(1)
                else:
                    print("Error: No JSON array brackets found in AI response.", flush=True)
                    time.sleep(1)
            else:
                print(f"API Error {response.status_code}: {response.text}", flush=True)
                time.sleep(1)
        except Exception as e:
            print(f"Connection Exception: {str(e)}", flush=True)
            time.sleep(1)
            
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

def draw_stamp(img_w, img_h, score_text, lang_code):
    base_font_size = int(img_h * 0.04)
    stamp_font = load_font(base_font_size)
    label_font = load_font(int(base_font_size * 0.4))
    
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    try:
        bbox = temp_draw.textbbox((0, 0), score_text, font=stamp_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = temp_draw.textsize(score_text, font=stamp_font)

    padding = int(img_w * 0.04)
    stamp_size = max(text_w, text_h) + (padding * 2)
    stamp = Image.new("RGBA", (stamp_size, stamp_size), (255, 255, 255, 0))
    s_draw = ImageDraw.Draw(stamp)
    
    out_m = int(stamp_size * 0.03)
    in_m = int(stamp_size * 0.12)
    out_w = max(2, int(stamp_size * 0.03))
    in_w = max(1, int(stamp_size * 0.01))

    s_draw.ellipse([out_m, out_m, stamp_size-out_m, stamp_size-out_m], fill=(255, 255, 255, 255), outline=COLOR_WRONG, width=out_w)
    s_draw.ellipse([in_m, in_m, stamp_size-in_m, stamp_size-in_m], outline=COLOR_WRONG, width=in_w)
    
    score_label = "SCORE"
    if lang_code == "FR": score_label = "NOTE"

    s_draw.text((stamp_size//2, int(stamp_size * 0.32)), score_label, fill=COLOR_WRONG, font=label_font, anchor="mm")
    s_draw.text((stamp_size//2, int(stamp_size * 0.65)), score_text, fill=COLOR_WRONG, font=stamp_font, anchor="mm")
    
    return stamp.rotate(-15, expand=True, resample=Image.BICUBIC)

# ==========================================
# ROUTE 2: API GRADING ENGINE
# ==========================================
@app.route('/api/grade', methods=['POST'])
def grade_api():
    if 'image' not in request.files or 'api_key' not in request.form:
        return Response("Missing image or api_key", status=400)
        
    file = request.files['image']
    api_key = request.form['api_key']
    lang_code = request.form.get('language', 'EN')
    
    lang_map = {"EN": "English", "FR": "French"}
    language_name = lang_map.get(lang_code, "English")

    if file.filename == '':
        return Response("No selected image", status=400)

    try:
        img_bytes = file.read()
        original_img = Image.open(io.BytesIO(img_bytes))
        original_img = ImageOps.exif_transpose(original_img).convert("RGBA")
        width, height = original_img.size
        
        overlay = Image.new("RGBA", original_img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        font_size = int(height * 0.016)
        font = load_font(font_size)
        line_w = max(2, int(height * 0.003))
        mark_scale = max(2, int(height * 0.006))
        
        occupied_rects = []
        
        api_img = original_img.copy().convert("RGB")
        api_img.thumbnail((1024, 1024))
        
        grading_results = get_api_annotations(api_img, api_key, language_name)

        if not grading_results:
            return Response("Failed to analyze the math. Check API key or Vercel logs.", status=500)

        valid_results = []
        total_possible_points = 0
        earned_points = 0

        for problem in grading_results:
            if not isinstance(problem, dict):
                continue

            for step in problem.get("lines", []):
                box = step.get("box_2d", [0, 0, 0, 0])
                if not box or len(box) != 4: continue
                
                top = int((box[0] / 1000.0) * height)
                left = int((box[1] / 1000.0) * width)
                bottom = int((box[2] / 1000.0) * height)
                right = int((box[3] / 1000.0) * width)
                
                if top > height * 0.85:
                    continue
                    
                step["global_box"] = [left, top, right, bottom]
                valid_results.append(step)

                status = step.get("status", "correct")
                total_possible_points += 2
                
                if status == "correct" or status == "error_carried_forward":
                    earned_points += 2
                elif status == "minor_error":
                    earned_points += 1

        stamp_x, stamp_y = 0, 0
        stamp_rect = [0, 0, 0, 0]
        stamp_img = None
        
        if total_possible_points > 0:
            raw_score = (earned_points / total_possible_points) * 20
            score_20 = round(raw_score * 2) / 2
            grade_text = f"{int(score_20)}/20" if score_20.is_integer() else f"{score_20}/20"

            stamp_img = draw_stamp(width, height, grade_text, lang_code)
            s_w, s_h = stamp_img.size

            stamp_x = width - s_w - int(width * 0.03)
            stamp_y = int(height * 0.03)
            stamp_rect = [stamp_x, stamp_y, stamp_x + s_w, stamp_y + s_h]
            occupied_rects.append(stamp_rect) 

        for step in valid_results:
            left, top, right, bottom = step["global_box"]
            status = step.get("status", "correct")

            box_cy = top + (bottom - top) // 2
            
            mark_x = width - int(width * 0.06) 
            mark_y = box_cy

            if stamp_img and (stamp_rect[1] - (mark_scale*5) <= mark_y <= stamp_rect[3] + (mark_scale*5)):
                mark_x = stamp_rect[0] - int(width * 0.04)

            temp_mark_rect = [mark_x - (mark_scale*3), mark_y - (mark_scale*3), mark_x + (mark_scale*5), mark_y + (mark_scale*5)]
            occupied_rects.append(temp_mark_rect)

            draw_right = min(right, mark_x - int(width * 0.03))
            step["draw_right"] = draw_right 
            
            occupied_rects.append([left, top, draw_right, bottom])

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

        for step in valid_results:
            status = step.get("status", "correct")
            feedback = step.get("feedback", "")
            if not feedback: continue
            
            left, top, right, bottom = step["global_box"]
            draw_right = step["draw_right"]
            box_cx = left + (draw_right - left) // 2
            box_cy = top + (bottom - top) // 2

            if status in ["minor_error", "conceptual_error"]:
                error_color = COLOR_MINOR if status == "minor_error" else COLOR_WRONG

                char_width_estimate = int(width * 0.015) 
                max_chars = max(15, int((width * 0.25) / char_width_estimate))
                wrapped_feedback = "\n".join(textwrap.wrap(feedback, width=max_chars, break_long_words=False))

                try:
                    bbox = draw.textbbox((0, 0), wrapped_feedback, font=font)
                    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    text_w, text_h = draw.textsize(wrapped_feedback, font=font)
                    
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
                
                # FIXED: Increased from 0.3 to 0.5 to push the text beautifully into the true center!
                text_offset_y = int(pad_y * 0.5)
                draw.text((note_rect[0] + pad_x, note_rect[1] + text_offset_y), wrapped_feedback, fill=error_color, font=font)

        if stamp_img:
            overlay.paste(stamp_img, (stamp_x, stamp_y), stamp_img)

        final_img = Image.alpha_composite(original_img, overlay).convert("RGB")
        
        output_io = io.BytesIO()
        final_img.save(output_io, format="JPEG", quality=90)
        output_io.seek(0)
        
        return send_file(output_io, mimetype="image/jpeg")

    except Exception as e:
        print(f"Server Error in grade_api: {str(e)}", flush=True)
        return Response(f"Internal Server Error: {str(e)}", status=500)
