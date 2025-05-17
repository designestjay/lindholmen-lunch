# file: lindholmen_lunch/generate_html.py

import json
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from pathlib import Path

def generate_lunch_summary(day: str):
    data_path = f"data/lunch_data_{day}.json"
    if not os.path.exists(data_path):
        print(f"[WARN] No data file for {day}: {data_path}")
        return

    with open(data_path, encoding="utf-8") as f:
        lunch_data = json.load(f)

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("summary_template.html")

    output_html = template.render(
        day=day.capitalize(),
        lunch_data=lunch_data,
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    os.makedirs("docs", exist_ok=True)
    output_path = f"docs/lunch_{day}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_html)

    print(f"[INFO] Generated HTML summary for {day}: {output_path}")


def generate_index_page():
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)

    # Map lowercase filenames to proper weekday labels
    weekday_order = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    weekday_labels = {
        "monday": "Måndag",
        "tuesday": "Tisdag",
        "wednesday": "Onsdag",
        "thursday": "Torsdag",
        "friday": "Fredag"
    }

    # Collect available files and sort by weekday order
    lunch_files = {f.stem.replace("lunch_", ""): f for f in output_dir.glob("lunch_*.html")}
    ordered_links = [
        (day, lunch_files[day]) for day in weekday_order if day in lunch_files
    ]

    # Build HTML
    html = """<html><head><meta charset='utf-8'>
    <style>
    body { font-family: Arial, sans-serif; background: #f8f8f8; padding: 20px; }
    h1 { color: #004d66; }
    .button-container { margin-top: 30px; display: flex; flex-direction: column; gap: 15px; max-width: 400px; }
    .weekday-button {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #004d66;
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-size: 18px;
        text-decoration: none;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: background 0.2s ease;
    }
    .weekday-button:hover { background: #006080; }
    .timestamp {
        font-size: 13px;
        font-weight: normal;
        color: #ccc;
    }
    </style>
    </head><body>
    <h1>Lunchmeny för veckan i Lindholmen</h1>
    <div class="button-container">
    """

    for day, file in ordered_links:
        label = weekday_labels[day]
        ts = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        html += f"""
        <a class="weekday-button" href="{file.name}">
            <span>{label}</span>
            <span class="timestamp">{ts}</span>
        </a>
        """

    html += """
    </div>
    </body></html>
    """

    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"[INFO] Generated weekly index page: {index_path}")