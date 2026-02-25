import streamlit as st
import pandas as pd
import os
import json
import uuid
import time  # NEW: Imported for rate-limit cooldown
from google import genai
from pydantic import BaseModel, Field
from typing import Optional

# --- 1. PAGE SETUP & STYLE (Only once!) ---
st.set_page_config(page_title="INKOS | Industrial Batch", page_icon="⚙️", layout="wide")

# Custom CSS for the "Industrial" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    div[data-testid="stExpander"] { border: 1px solid #00ffa2; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER SECTION ---
col_title, col_stats = st.columns([4, 2])
with col_title:
    st.title("⚙️ Industrial Batch Spec-Extractor")
    st.write("Drag and drop multiple equipment datasheets (PDFs) below to compile a technical database.")

with col_stats:
    m1, m2 = st.columns(2)
    m1.metric("Engine", "Gemini 2.5 Flash")
    m2.metric("Tier", "Free Tier", delta="Rate-Limited")

st.divider()

# Check for API Key
if "GEMINI_API_KEY" not in os.environ:
    st.error("⚠️ GEMINI_API_KEY environment variable is not set in Secrets.")
    st.stop()

client = genai.Client()

# --- 3. THE BLUEPRINT ---
class CompressorSpecs(BaseModel):
    model_name: str = Field(description="The general model name of the compressor")
    max_supported_power_kw: Optional[float] = Field(default=None, description="Motor power in kW")
    aerodynamic_efficiency_percent: Optional[float] = Field(default=None, description="Max aerodynamic efficiency")
    max_motor_shaft_speed_rpm: Optional[int] = Field(default=None, description="Motor shaft speed in RPM")
    rated_motor_current_amps: Optional[float] = Field(default=None, description="Rated motor current in Amps")
    weight_kg: Optional[float] = Field(default=None, description="Weight in kg")
    cooling_medium: Optional[str] = Field(default=None, description="Type of cooling medium")
    pros_and_cons_summary: str = Field(description="Write a 1-sentence summary of the main pros and cons.")

# --- 4. BATCH FILE UPLOADER ---
uploaded_files = st.file_uploader("Upload PDF Datasheets", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 Extract Data from All Files"):
        all_extracted_data = []
        progress_text = "Analyzing Engineering Specs..."
        my_bar = st.progress(0, text=progress_text)
        
        # Enumerate to track our current position in the batch
        for i, uploaded_file in enumerate(uploaded_files):
            temp_pdf_path = f"temp_{uuid.uuid4().hex}.pdf"
            gemini_file = None 
            
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            try:
                # 1. Upload to Gemini Storage
                gemini_file = client.files.upload(file=temp_pdf_path)
                
                # 2. Extract Data
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[gemini_file, "Extract the technical specifications. Leave missing specs as null."],
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': CompressorSpecs,
                    },
                )
                
                # 3. Save Data
                data_dict = json.loads(response.text)
                data_dict["source_file"] = uploaded_file.name
                all_extracted_data.append(data_dict)
                
            except Exception as e:
                st.warning(f"⚠️ Failed to process {uploaded_file.name}. Error: {e}")
                
            finally:
                # 4. CLEANUP: Delete from Google's servers
                if gemini_file:
                    try:
                        client.files.delete(name=gemini_file.name)
                    except Exception as cleanup_error:
                        st.sidebar.error(f"Failed to delete {gemini_file.name} from API: {cleanup_error}")
                
                # 5. CLEANUP: Delete the local temporary file
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path) 
            
            # Update progress bar
            percent_complete = int(((i + 1) / len(uploaded_files)) * 100)
            my_bar.progress(percent_complete, text=f"Processed {uploaded_file.name}...")

            # NEW: Free Tier Rate Limit Protection
            # Skip the sleep if it's the very last file in the batch
            if i < len(uploaded_files) - 1:
                with st.spinner(f"⏳ Cooling down to respect API limits (Processing next file shortly)..."):
                    time.sleep(4)

        st.success("Batch Extraction Complete!")
        
        # --- 5. DISPLAY AND DOWNLOAD ---
        if all_extracted_data:
            df = pd.DataFrame(all_extracted_data)
            
            # Reorder columns to put source_file and model_name first
            cols = ['source_file', 'model_name'] + [c for c in df.columns if c not in ['source_file', 'model_name']]
            df = df[cols]
            
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            
            # Using primary button type to make it pop just like the invoice one
            st.download_button(
                label="⬇️ DOWNLOAD MASTER BATCH CSV", 
                data=csv, 
                file_name="industrial_specs_master.csv", 
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        else:
            st.error("No data was successfully extracted.")
