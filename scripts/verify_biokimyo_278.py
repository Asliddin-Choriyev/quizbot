import csv
from pathlib import Path

csv_path = Path("data/biokimyo_collections/biokimyo_variantli_209.csv")
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows in CSV: {len(rows)}")
assert len(rows) == 278, f"Expected 278 rows, found {len(rows)}"

for idx, r in enumerate(rows):
    q = r["question"]
    oa = r["option_a"]
    ob = r["option_b"]
    oc = r["option_c"]
    od = r["option_d"]
    ca = r["correct_answer"]
    exp = r["explanation"]
    
    assert len(q) > 0, f"Row {idx+1} question is empty"
    assert len(q) <= 295, f"Row {idx+1} question too long: {len(q)}"
    assert len(oa) <= 95, f"Row {idx+1} opt_a too long: {len(oa)}"
    assert len(ob) <= 95, f"Row {idx+1} opt_b too long: {len(ob)}"
    assert len(oc) <= 95, f"Row {idx+1} opt_c too long: {len(oc)}"
    assert len(od) <= 95, f"Row {idx+1} opt_d too long: {len(od)}"
    
    opts = [oa, ob, oc, od]
    assert len(set(opts)) == 4, f"Row {idx+1} has duplicates: {opts}"
    assert ca in ["A", "B", "C", "D"], f"Row {idx+1} invalid correct_answer: {ca}"
    assert len(exp) <= 200, f"Row {idx+1} explanation too long: {len(exp)}"

print("All 278 rows verified successfully!")
print("Row 210 (first new question):", rows[209])
print("Row 278 (last question):", rows[277])
