# CV-Handleiding Data Extractor

A Streamlit application that uses the Gemini 2.5 Flash API to extract technical data from HVAC (CV/Heat Pump) installation manuals in PDF format.

## Features
- PDF Uploading
- AI-powered technical data extraction (JSON format)
- Specifically tuned for Dutch HVAC terminology (G25.3 gas types, CO2/O2 ranges, etc.)
- Downloadable JSON output

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run main.py
   ```