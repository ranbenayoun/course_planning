# Technion Course Prerequisite Tree Web App

## Overview
This web application displays the prerequisite tree for Technion courses, using data from a PDF catalog and a JSON file. It shows all prerequisites for a selected course, recursively, and only displays courses that are present in the PDF-extracted list. If a prerequisite is missing, its entire branch is omitted from the tree.

## Features
- Select a course and view its full prerequisite tree.
- Only courses present in the PDF are shown.
- Prerequisite branches with missing courses are omitted.
- Clean, modern web interface (Flask + HTML/CSS).

## Files
- `app.py` — Main Flask application.
- `courses.json` — Course data (with prerequisites and course numbers).
- `bme_catalog_2025-2026.pdf` — PDF catalog used to extract allowed courses.
- `requirements.txt` — Python dependencies.

## Setup Instructions
1. **Install Python 3.8+** (recommended: use a virtual environment)
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Run the app:**
   ```
   python app.py
   ```
4. **Open your browser:**
   Go to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## How it Works
- The app loads course data from `courses.json` and extracts allowed courses from the PDF.
- When a course is selected, it builds a tree of prerequisites, recursively.
- Each branch of prerequisites (separated by parentheses in the JSON) is only shown if all its courses are present in the PDF list.

## Customization
- To update the course list, replace `courses.json` and/or the PDF file.
- The prerequisite parsing logic is in `app.py` (see `get_requirements`).

## Contact
For questions or further development, contact the original author or open an issue if hosted on a repository.

## Acknowledgments
The technion-sap-info-fecher was created by Michael Maltsev (from Cheesfork fame) and can be found at https://github.com/michael-maltsev/technion-sap-info-fetcher 
The project was inspired by Lior Romano
