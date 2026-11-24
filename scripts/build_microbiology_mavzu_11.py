import os
import re
import csv
import random
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageChops

# Set seed for reproducibility
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
COLLECTIONS_DIR = DATA_DIR / "mikrobiologiya_collections"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795496292858_9e9bec4d.pdf"

# Specific coordinate mapping for the 12 image questions: (page_index_0_based, y1_q, y0_ans)
IMG_MAP = {
    33: (2, 63.1, 179.6),
    34: (2, 209.1, 330.8),
    35: (2, 360.3, 482.9),
    36: (2, 512.4, 649.5),
    37: (3, 63.1, 200.2),
    38: (3, 229.7, 331.8),
    73: (5, 122.1, 218.5),
    74: (5, 261.0, 361.9),
    75: (5, 404.4, 466.2),
    76: (5, 495.7, 600.4),
    77: (5, 629.9, 734.6),
    78: (6, 63.1, 167.9),
}

DOMAIN_POOLS = {
    "immunology_branches": [
        "Immunogenetika", "Immunogematologiya", "Immunoterapiya",
        "Immunodiagnostika", "Immunologiya", "Transplantatsion immunologiya"
    ],
    "immunoglobulins": [
        "IgG", "IgM", "IgA", "IgE", "IgD", "Sekretor IgA", "Sekretor Ig"
    ],
    "antigens": [
        "H-antigen (xivchin)", "O-antigen (hujayra devori)",
        "K-antigen (kapsula)", "F-antigen (kiprikcha)", "Vi-antigen"
    ],
    "antigen_letters": [
        "H", "O", "K", "F", "Vi"
    ],
    "antigen_types": [
        "H-antigen", "O-antigen", "K-antigen", "F-antigen", "Vi-antigen"
    ],
    "scientists": [
        "I.I. Mechnikov", "P. Erlix", "L. Paster", "R. Kox", "Kastellani", "J. Borde"
    ],
    "fagocitoz_stages": [
        "Xemotaksis", "Adgeziya", "Endositoz", "Xemotaksis (fagotsitoz)",
        "Adgeziya (fagotsitoz)", "Endositoz (fagotsitoz)", "Dezintegratsiya"
    ],
    "vaccines": [
        "Tirik vaksinalar", "Inaktivatsiyalangan (o'ldirilgan) vaksinalar",
        "Kimyoviy vaksinalar", "Anatoksinlar", "Rekombinant vaksinalar", "Autovaksina"
    ],
    "vaccine_names": [
        "AKDS", "BTSJ", "VGV-1", "OPV (poliomiyelit)", "Qizamiqqa qarshi vaksina"
    ],
    "lab_vessels": [
        "Buyum oynachasida", "Probirkalarda", "Polistirol planshet", "Petri kosachasida"
    ],
    "cells": [
        "Plazmatik hujayralar (B-limfotsitlardan)", "T-limfotsitlar",
        "Makrofaglar", "Neytrofillar", "Eritrotsitlar"
    ],
    "t_cells": [
        "Yordamchi T-hujayra", "O'ldiruvchi", "Supressor T-hujayra", "Effektor T-hujayra"
    ],
    "organs": [
        "Timus", "Timus, suyak ko'migi, fabritsus haltachasi",
        "Bodomsimon bezlar, Peyer pilakchalari, taloq, chuvalchangsimon o'simta",
        "Jigar va taloq", "Limfa tugunlari"
    ]
}

def trim_image(im: Image.Image) -> Image.Image:
    bg = Image.new(im.mode, im.size, (255, 255, 255) if im.mode == 'RGB' else (255, 255, 255, 255))
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        w, h = im.size
        pad_bbox = (max(0, bbox[0]-2), max(0, bbox[1]-2), min(w, bbox[2]+2), min(h, bbox[3]+2))
        return im.crop(pad_bbox)
    return im

def clean_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def extract_images(doc):
    saved_images = {}
    for q_num, (p_no, y1, y0) in IMG_MAP.items():
        page = doc[p_no]
        clip = fitz.Rect(50, y1 + 1, page.rect.width - 50, y0 - 1)
        pix = page.get_pixmap(clip=clip, dpi=180)
        im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        trimmed = trim_image(im)
        filename = f"mikro_m11_q{q_num:03d}.png"
        out_file = IMAGES_DIR / filename
        trimmed.save(out_file, format='PNG', optimize=True)
        rel_path = f"data/images/{filename}"
        saved_images[q_num] = rel_path
        print(f"Extracted image for Q{q_num} -> {filename}")
    return saved_images

def generate_distractors(correct_ans: str, question_text: str, all_answers: list) -> list:
    norm_ans = correct_ans.strip().rstrip('.')
    low_ans = norm_ans.lower()

    # 1. True / False
    if low_ans in ["to'g'ri", "ha", "to‘g‘ri", "to'g'ri."]:
        return ["Yo'q (Noto'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
    if low_ans in ["yo'q", "yo‘q", "noto'g'ri", "yo'q."]:
        return ["Ha (To'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]

    # 2. Number sequences
    if norm_ans == "1, 2, 3, 4":
        return ["1, 3, 5, 7", "2, 4, 6", "1, 2, 5, 6"]
    if "3, 4, 5, 6" in norm_ans:
        return ["Musbat: 1, 2-probirkalar", "Musbat: faqat 1-probirka", "Manfiy: barcha probirkalar"]
    if '1, 2, 3, 4 ("zontik"' in norm_ans:
        return [
            "5, 6, 7 ('tugmacha' cho'kma)",
            "1 va 2 ('nuqta' cho'kma)",
            "Barcha probirkalarda musbat"
        ]
    if "2-rasm; cho'kma" in low_ans:
        return [
            "1-rasm; eritma tiniq bo'lsa",
            "1 va 2-rasmlar ikkalasi ham musbat",
            "Ikkala holatda ham manfiy"
        ]

    # 3. Specific terms
    if low_ans == "2 oylikdan":
        return ["3 oylikdan", "6 oylikdan", "1 yoshdan"]
    if "xalqaro birlik" in low_ans:
        return ["Milligramm (mg)", "Titr ko'rsatkichi", "Bakterial birlik"]
    if "alfa, beta, gamma" in low_ans:
        return ["Alfa, delta, omega", "Gamma, epsilon, kappa", "Alfa va beta"]
    if low_ans == "profilaktika":
        return ["Davolash", "Diagnostika", "Reabilitatsiya"]
    if low_ans == "qoqshol":
        return ["Difteriya", "Botulizm", "Quturish"]
    if low_ans == "trivaksina":
        return ["Monovaksina", "Divaksina", "Polivaksina (pentavaksina)"]

    # 4. Domain pools
    for pool_name, pool in DOMAIN_POOLS.items():
        matched = False
        for item in pool:
            if item.lower() == low_ans or (len(item) > 3 and item.lower() in low_ans):
                matched = True
                break
        if matched:
            cands = [p for p in pool if p.lower() != low_ans and p.lower() not in low_ans and low_ans not in p.lower()]
            random.shuffle(cands)
            if len(cands) >= 3:
                return cands[:3]

    # 5. Fallback from all topic answers of similar length
    target_len = len(norm_ans)
    clean_all = []
    seen = {low_ans}
    for a in all_answers:
        ca = a.strip().rstrip('.')
        ca_low = ca.lower()
        if (ca_low not in seen
            and ca_low not in ["to'g'ri", "yo'q", "ha", "noto'g'ri"]
            and len(ca) <= 90 and len(ca) >= 3):
            seen.add(ca_low)
            clean_all.append(ca)

    clean_all.sort(key=lambda x: abs(len(x) - target_len))
    selected = clean_all[:3]

    defaults = [
        "Fagotsitoz jarayoni",
        "Komplement tizimi",
        "Spetsifik antitelolar",
        "T- va B-limfotsitlar"
    ]
    for d in defaults:
        if len(selected) >= 3:
            break
        if d.lower() not in [s.lower() for s in selected] and d.lower() != low_ans:
            selected.append(d)

    return selected[:3]

def build_collection():
    doc = fitz.open(PDF_PATH)
    
    # 1. Extract images
    print("Extracting images...")
    saved_images = extract_images(doc)
    
    # 2. Parse text
    full_text = ''
    for p_idx, page in enumerate(doc):
        full_text += f'\n---PAGE_{p_idx}---\n' + page.get_text()

    pattern = re.compile(r'(?:^|\n)\s*(\d+)\.\s*(.*?)\s*\n\s*Javob:\s*(.*?)(?=\n\s*\d+\.|\n---PAGE_|\Z)', re.DOTALL | re.IGNORECASE)
    matches = pattern.findall(full_text)
    print(f"Parsed {len(matches)} questions from PDF.")
    
    all_answers = [clean_text(m[2]) for m in matches]
    rows = []
    
    for num_str, q_body, ans_body in matches:
        num = int(num_str)
        q_text = clean_text(q_body)
        raw_ans = clean_text(ans_body)
        
        # True / False format
        if raw_ans.lower() in ["to'g'ri", "to‘g‘ri", "to'g'ri.", "ha"]:
            correct_opt = "Ha (To'g'ri)"
            distractors = ["Yo'q (Noto'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
        elif raw_ans.lower() in ["yo'q", "yo‘q", "yo'q.", "noto'g'ri"]:
            correct_opt = "Yo'q (Noto'g'ri)"
            distractors = ["Ha (To'g'ri)", "Qisman to'g'ri", "Faqat ayrim hollarda"]
        else:
            correct_opt = raw_ans.rstrip('.')
            distractors = generate_distractors(correct_opt, q_text, all_answers)
            
        correct_opt = correct_opt[:95]
        clean_distractors = [d[:95] for d in distractors[:3]]
        
        # Ensure 4 unique options
        seen_opts = {correct_opt.lower()}
        final_distractors = []
        for d in clean_distractors:
            if d.lower() not in seen_opts:
                seen_opts.add(d.lower())
                final_distractors.append(d)
                
        while len(final_distractors) < 3:
            filler = f"Variant {chr(66 + len(final_distractors))}"
            final_distractors.append(filler)
            
        all_opts = [correct_opt] + final_distractors
        random.shuffle(all_opts)
        correct_letter = chr(65 + all_opts.index(correct_opt))
        
        if len(q_text) > 295:
            q_text = q_text[:292] + "..."
            
        explanation = f"To'g'ri javob: {correct_opt}"
        if len(explanation) > 200:
            explanation = explanation[:197] + "..."
            
        img_path = saved_images.get(num, "")
        
        rows.append({
            "question": q_text,
            "option_a": all_opts[0],
            "option_b": all_opts[1],
            "option_c": all_opts[2],
            "option_d": all_opts[3],
            "correct_answer": correct_letter,
            "explanation": explanation,
            "topic": "Mikrobiologiya: 11-mavzu",
            "difficulty": "Medium",
            "timer": 25,
            "image": img_path
        })
        
    csv_filename = "mikrobiologiya_mavzu_11.csv"
    csv_path = COLLECTIONS_DIR / csv_filename
    with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question", "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
        ])
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Successfully generated {csv_path} with {len(rows)} questions ({sum(1 for r in rows if r['image'])} with images)!")

if __name__ == "__main__":
    build_collection()
