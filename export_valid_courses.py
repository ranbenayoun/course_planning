import json
import re
import pypdf

PDF_PATH = "bme_catalog_2025-2026.pdf"
COURSES_JSON_PATH = "courses.json"
OUTPUT_PATH = "valid_courses.json"

def extract_courses_from_pdf(pdf_path):
    courses = set()
    try:
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text() or ""
            # Extract 7 digit numbers
            matches = re.findall(r'\b\d{7}\b', text)
            for match in matches:
                # Prepend 0 to make it 8 digits as per user requirement
                courses.add("0" + match)
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return sorted(list(courses))

print("Loading courses.json...")
with open(COURSES_JSON_PATH, encoding="utf-8") as f:
    COURSES_DATA = json.load(f)

print("Extracting from PDF...")
extracted_courses = extract_courses_from_pdf(PDF_PATH)

# Filter to only courses present in courses.json
valid_ids_in_json = {course["general"].get("מספר מקצוע") for course in COURSES_DATA}
final_courses = [c for c in extracted_courses if c in valid_ids_in_json]

print(f"Found {len(final_courses)} valid courses.")

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(final_courses, f, ensure_ascii=False)

print(f"Saved to {OUTPUT_PATH}")
