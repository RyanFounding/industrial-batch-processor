# ⚙️ Industrial Datasheet Batch Processor
**Developed by INKOS**

This AI-driven tool is designed for Industrial Engineers to automate the tedious task of manual data entry from technical equipment datasheets.

### 🛠️ The Problem
Engineers often have to compare technical specifications (RPM, Power, Efficiency) across dozens of PDF catalogs from different vendors. This is slow, manual, and prone to error.

### 💡 The Solution
Using **Gemini 2.5 Flash**, this app extracts complex technical variables into a standardized, "SQL-ready" CSV database in seconds.

### 🚀 How to use
1. Visit the **https://inkos-industrial.streamlit.app/**
2. Upload the sample PDFs provided in this repository (e.g., `datasheet_atlas.pdf`).
3. Click "Extract" to see the unified data table.
4. Download the final CSV for your analysis.

**Tech Stack:** Python, Streamlit, Pydantic, Google Gemini API.
