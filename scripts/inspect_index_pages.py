from pathlib import Path

path = Path(r"Y:\Final yr project\Honours\gps-spoof-timesync\scripts\generate_perfect_report.py")
text = path.read_text(encoding="utf-8")

for name in ["toc_data = [", "tables_meta = [", "figures_meta = ["]:
    idx = text.find(name)
    if idx != -1:
        print(f"=== {name} ===")
        print(text[idx:idx+2000])
        print("="*60)
