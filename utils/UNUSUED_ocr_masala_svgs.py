import os
from pathlib import Path
import cairosvg
import pytesseract
from PIL import Image
import json
import re

# Configuration
LANG = "swe"
INPUT_DIR = Path("tests/samples/sample_masala_images")
OUTPUT_JSON = "masala_lunch_all_weeks.json"

# Optional: uncomment and set path if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def svg_to_png(svg_path, scale_factor=3):
    """
    Converts SVG to PNG with increased resolution for better OCR.
    `scale_factor` multiplies the default size.
    """
    png_path = svg_path.with_suffix(".png")
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        dpi=96 * scale_factor  # default DPI * scale factor
    )
    return png_path

def extract_dishes_from_text(text: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = []
    current_name = None
    current_desc = []
    waiting_for_dash = False

    # Skip weekday
    lines = lines[1:]

    for line in lines:
        line = line.replace("–", "-").replace("—", "-").strip()

        # Ignore obvious junk like "Fd", "-", or single characters
        if line in {"-", "–", "—"} or len(line) <= 2:
            continue

        # If we're waiting for a dash to confirm the name-description break
        if waiting_for_dash and line == "-":
            continue
        elif waiting_for_dash:
            current_desc.append(line)
            waiting_for_dash = False
            continue

        # Likely a name if ALL CAPS or looks like a dish
        is_probable_name = re.match(r'^[A-ZÅÄÖ][A-ZÅÄÖA-Za-z\s]{4,}$', line)

        if is_probable_name:
            # Save previous item if exists
            if current_name:
                result.append({
                    "name": current_name.strip(),
                    "description": " ".join(current_desc).strip()
                })
            current_name = line
            current_desc = []
            waiting_for_dash = True  # Expect a dash line before description
        else:
            current_desc.append(line)

    # Final item
    if current_name:
        result.append({
            "name": current_name.strip(),
            "description": " ".join(current_desc).strip()
        })

    return result



def process_image(file: Path):
    png_path = svg_to_png(file)
    img = Image.open(png_path)
    custom_config = r'--oem 3 --psm 11'
    text = pytesseract.image_to_string(img, lang=LANG, config=custom_config)
    with open(file.with_suffix(".txt"), "w", encoding="utf-8") as debug_file:
        debug_file.write(text)
    png_path.unlink()  # Cleanup
    return extract_dishes_from_text(text)


def process_all_weeks(directory: Path):
    result = {
        "standing": [],
        "sides": [],
        "weeks": {}
    }

    for file in sorted(directory.glob("masala_lunch*.svg")):
        name = file.stem.lower()

        if "standing" in name:
            result["standing"] = process_image(file)
        elif "sides" in name:
            result["sides"] = process_image(file)
        elif "lunch" in name:
            parts = name.split("_")
            week = f"week{parts[1][-1]}"
            day = parts[-1].capitalize()

            if week not in result["weeks"]:
                result["weeks"][week] = {}
            result["weeks"][week][day] = process_image(file)

    return result

# Process all
data = process_all_weeks(INPUT_DIR)

# Save
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"[DONE] OCR extracted data saved to {OUTPUT_JSON}")
