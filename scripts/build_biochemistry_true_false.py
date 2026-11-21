import os
import re
import csv
from pathlib import Path
import pymupdf as fitz

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COLLECTIONS_DIR = DATA_DIR / "biokimyo_collections"
COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = r"C:\Users\user\.gemini\antigravity\brain\ac9f3884-a13d-489a-b6bd-7651e64730bb\.user_uploaded\media_1795251390085_d378a63f.pdf"

def clean_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def parse_pdf():
    doc = fitz.open(PDF_PATH)
    questions = []
    
    # We will iterate through blocks on each page
    for p_idx, page in enumerate(doc):
        blocks = page.get_text('blocks')
        current_num = None
        current_text = ""
        
        # Merge all block texts on the page to accurately capture question and answer
        page_text = page.get_text()
        # Find lines or blocks
        # Pattern: digits followed by dot, question text, then Javob: Ha/Yo'q
        # Note: some questions span multiple lines
        pattern = re.compile(r'(\d+)\.\s*(.*?)\s*Javob:\s*(Ha|Yo[\'`‘’\"]?q)', re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(page_text)
        print(f"Page {p_idx+1}: found {len(matches)} matches")
        for num_str, q_body, ans_str in matches:
            num = int(num_str)
            q_clean = clean_text(q_body)
            ans_clean = clean_text(ans_str)
            # Determine correct option
            if ans_clean.lower() in ["ha", "ha.", "to'g'ri"]:
                correct_letter = "A"
                exp = "To'g'ri javob: Ha"
            else:
                correct_letter = "B"
                exp = "To'g'ri javob: Yo'q"
                
            questions.append({
                "num": num,
                "question": q_clean,
                "option_a": "Ha",
                "option_b": "Yo'q",
                "option_c": "",
                "option_d": "",
                "correct_answer": correct_letter,
                "explanation": exp,
                "topic": "Biokimyo: Ha / Yo'q testlari",
                "difficulty": "Medium",
                "timer": 20,
                "image": ""
            })
            
    return questions

def main():
    questions = parse_pdf()
    print(f"Total questions parsed: {len(questions)}")
    
    # Validate sequential numbers
    nums = [q["num"] for q in questions]
    print(f"Question IDs: min={min(nums)}, max={max(nums)}, total={len(nums)}")
    missing = [x for x in range(1, max(nums)+1) if x not in nums]
    print(f"Missing IDs: {missing}")
    
    # Save to CSV
    csv_path = COLLECTIONS_DIR / "biokimyo_ha_yoq_68.csv"
    with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question", "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "explanation", "topic", "difficulty", "timer", "image"
        ])
        writer.writeheader()
        for q in questions:
            row = dict(q)
            row.pop("num")
            # Ensure telegram limits
            if len(row["question"]) > 295:
                row["question"] = row["question"][:292] + "..."
            writer.writerow(row)
            
    print(f"Saved {csv_path} with {len(questions)} questions.")

if __name__ == "__main__":
    main()
