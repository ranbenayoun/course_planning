import sys
import os
import re
import json
from flask import Flask, render_template_string, request
import pypdf

app = Flask(__name__)

PDF_PATH = "bme_catalog_2025-2026.pdf"
COURSES_JSON_PATH = "courses.json"

# Load all course data from courses.json at startup
with open(COURSES_JSON_PATH, encoding="utf-8") as f:
    COURSES_DATA = json.load(f)

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

ALLOWED_COURSES = []

# Cache for course data to avoid re-fetching in the same session
COURSE_CACHE = {}

def get_course_from_json(course_id):
    for course in COURSES_DATA:
        if course["general"].get("מספר מקצוע") == course_id:
            return course
    raise ValueError(f"Course {course_id} not found in courses.json")

def get_requirements(course_id, visited=None):
    if visited is None:
        visited = set()
    if course_id in visited:
        return {"id": course_id, "name": "Cycle Detected", "reqs": []}
    visited.add(course_id)
    # Check cache
    if course_id in COURSE_CACHE:
        data = COURSE_CACHE[course_id]
    else:
        try:
            data = get_course_from_json(course_id)
            COURSE_CACHE[course_id] = data
        except Exception as e:
            return {"id": course_id, "name": f"Error: {e}", "reqs": [], "req_str": ""}
    general = data.get('general', {})
    name = general.get('שם מקצוע', '')
    reqs_str = general.get('מקצועות קדם', '')
    # Split branches by () and treat each branch as a group of prereqs (AND within branch, OR between branches)
    # Find all branches inside parentheses
    branch_matches = re.findall(r'\(([^()]*)\)', reqs_str)
    # If no parentheses, treat the whole string as a single branch
    if not branch_matches:
        branch_matches = [reqs_str]
    branch_nodes = []
    for branch in branch_matches:
        req_ids = re.findall(r'\d{8}', branch)
        if not req_ids:
            continue
        branch_has_missing = False
        branch_children = []
        for req_id in req_ids:
            if req_id in ALLOWED_COURSES:
                child = get_requirements(req_id, visited=visited.copy())
                if child.get('missing'):
                    branch_has_missing = True
                branch_children.append(child)
            else:
                branch_has_missing = True
        # Only add branch if all courses are present (not missing)
        if not branch_has_missing:
            # Represent the branch as a group (AND)
            if len(branch_children) == 1:
                branch_nodes.append(branch_children[0])
            else:
                branch_nodes.append({
                    "id": " & ".join([c["id"] for c in branch_children]),
                    "name": "דרישות קדם: " + ", ".join([c["name"] for c in branch_children]),
                    "reqs": branch_children,
                    "req_str": branch,
                })
    return {"id": course_id, "name": name, "reqs": branch_nodes, "req_str": reqs_str}

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_course = None
    tree_data = None
    if request.method == 'POST':
        selected_course = request.form.get('course')
        if selected_course:
            tree_data = get_requirements(selected_course)
    return render_template_string(HTML_TEMPLATE, courses=ALLOWED_COURSES, selected=selected_course, tree=tree_data)

HTML_TEMPLATE = """
{% macro render_tree(node) %}
    <div class="node-wrapper">
        <div class="node" style="{% if node.missing %}background-color: #eee; color: #888; border-color: #ccc;{% endif %}">
            <span class="course-id">{{ node.id }}</span> {{ node.name }}
            {% if node.req_str %}
                <span class="req-str">דרישות קדם: {{ node.req_str }}</span>
            {% endif %}
        </div>
        {% if node.reqs %}
            <ul>
                {% for child in node.reqs %}
                    <li>{{ render_tree(child) }}</li>
                {% endfor %}
            </ul>
        {% endif %}
    </div>
{% endmacro %}
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <title>Technion Course Planner</title>
    <style>
        body { font-family: sans-serif; padding: 20px; background-color: #f9f9f9; }
        h1 { color: #333; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        select { padding: 10px; font-size: 16px; margin-left: 10px; }
        button { padding: 10px 20px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        ul { list-style-type: none; padding-right: 20px; border-right: 2px solid #eee; margin-right: 10px; }
        li { margin: 10px 0; position: relative; }
        li::before {
            content: '';
            position: absolute;
            top: 15px;
            right: -22px;
            width: 20px;
            height: 1px;
            background: #ccc;
        }
        .node { 
            border: 1px solid #ddd; 
            padding: 10px; 
            border-radius: 4px; 
            background-color: #fff; 
            display: inline-block;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .req-str { font-size: 0.85em; color: #777; display: block; margin-top: 4px; }
        .course-id { font-weight: bold; color: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>מתכנן מערכת שעות - הנדסה ביו-רפואית</h1>
        <p>בחר קורס מהרשימה כדי לראות את עץ הקדמים שלו.</p>
        <form method="POST">
            <label for="course">בחר קורס:</label>
            <select name="course" id="course">
                <option value="" disabled {% if not selected %}selected{% endif %}>בחר...</option>
                {% for course in courses %}
                    <option value="{{ course }}" {% if course == selected %}selected{% endif %}>{{ course }}</option>
                {% endfor %}
            </select>
            <button type="submit">הצג דרישות</button>
        </form>
        {% if tree %}
            <hr>
            <h2>דרישות עבור: <span dir="ltr">{{ tree.id }}</span> - {{ tree.name }}</h2>
            <div class="tree-container">
                {{ render_tree(tree) }}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    print("Extracting courses from PDF...")
    ALLOWED_COURSES = extract_courses_from_pdf(PDF_PATH)
    # Filter to only courses present in courses.json
    valid_course_ids = {course["general"].get("מספר מקצוע") for course in COURSES_DATA}
    ALLOWED_COURSES = [c for c in ALLOWED_COURSES if c in valid_course_ids]
    print(f"Loaded {len(ALLOWED_COURSES)} valid courses from catalog.")
    app.run(host='0.0.0.0', port=5000)