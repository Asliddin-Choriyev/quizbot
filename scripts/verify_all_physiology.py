import csv
from pathlib import Path

csv_dir = Path("data/fiziologiya_collections")
files = sorted(csv_dir.glob("fiziologiya_mavzu_*.csv"))

print(f"Found {len(files)} CSV files in {csv_dir}")
assert len(files) == 12, f"Expected 12 files, found {len(files)}"

total_rows = 0
for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    num_rows = len(rows)
    total_rows += num_rows
    print(f"{fpath.name}: {num_rows} questions")
    
    for idx, r in enumerate(rows):
        q = r["question"]
        oa = r["option_a"]
        ob = r["option_b"]
        oc = r["option_c"]
        od = r["option_d"]
        ca = r["correct_answer"]
        exp = r["explanation"]
        top = r["topic"]
        
        assert len(q) > 0, f"{fpath.name} #{idx+1} question is empty"
        assert len(q) <= 295, f"{fpath.name} #{idx+1} question too long: {len(q)}"
        
        assert len(oa) <= 95, f"{fpath.name} #{idx+1} opt_a too long: {len(oa)}"
        assert len(ob) <= 95, f"{fpath.name} #{idx+1} opt_b too long: {len(ob)}"
        assert len(oc) <= 95, f"{fpath.name} #{idx+1} opt_c too long: {len(oc)}"
        assert len(od) <= 95, f"{fpath.name} #{idx+1} opt_d too long: {len(od)}"
        
        # Check all 4 options are distinct
        opts = [oa, ob, oc, od]
        assert len(set(opts)) == 4, f"{fpath.name} #{idx+1} has duplicate options: {opts}"
        
        assert ca in ["A", "B", "C", "D"], f"{fpath.name} #{idx+1} invalid correct_answer: {ca}"
        assert len(exp) <= 200, f"{fpath.name} #{idx+1} explanation too long: {len(exp)}"
        assert len(top) > 0, f"{fpath.name} #{idx+1} topic is empty"

print(f"\nALL CHECKS PASSED PERFECTLY! Total verified questions: {total_rows}")
