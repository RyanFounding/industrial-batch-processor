# ⚙️ Industrial Datasheet Batch Processor
**Developed by INKOS**

A specialized engineering tool designed to automate the extraction of technical specifications from unstructured industrial PDF catalogs.

### 🛠️ The Problem
Industrial Engineers often spend hours manually comparing equipment specs (RPM, Power, Efficiency, Weight) across hundreds of vendor PDFs. This process is slow, prone to transcription errors, and delays decision-making in procurement and system design.

### 💡 The Solution
This tool uses a **multi-file batch pipeline** powered by **Gemini 2.5 Flash**. It allows an engineer to upload an entire folder of datasheets simultaneously. The AI extracts technical variables into a unified, standardized database for instant side-by-side comparison.

### 🚀 Live Demo
**Try the Batch Processor here:** [https://inkos-industrial.streamlit.app/](https://inkos-industrial.streamlit.app/)

### 📖 How to Use
1. Launch the **Live Demo** link above.
2. Drag and drop the sample datasheets provided in this repository (e.g., `datasheet_atlas.pdf`, `datasheet_elgi.pdf`).
3. Click **"Extract Data from All Files"** to begin the batch process.
4. Review the compiled specification table and click **"Download Batch CSV"** for your analysis.

### 🏗️ Technical Stack
* **AI Model:** Google Gemini 2.5 Flash
* **Framework:** Streamlit (Batch File Handling)
* **Data Logic:** Pydantic & Pandas (Tabular Compilation)
