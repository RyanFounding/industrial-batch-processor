import streamlit as st
import pandas as pd
import os
import json
from google import genai
from pydantic import BaseModel, Field
from typing import Optional

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Industrial Batch Processor", page_icon="⚙️")
st.title("⚙️ Industrial Datasheet Batch Processor")
st.write("Drag and drop multiple equipment datasheets (PDFs) below. The AI will extract the technical specifications and compile them into a single database.")

# Check for API Key
if "GEMINI_API_KEY" not in os.environ:
    st.error("⚠️ GEMINI_API_KEY environment variable is not set.")
    st.stop()

client = genai.Client()

# --- 2. THE BLUEPRINT ---
class CompressorSpecs(BaseModel):
    model_name: str = Field(description="The general model name of the compressor")
    max_supported_power_kw: Optional[float] = Field(default=None, description="Motor power in kW")
    aerodynamic_efficiency_percent: Optional[float] = Field(default=None, description="Max aerodynamic efficiency")
    max_motor_shaft_speed_rpm: Optional[int] = Field(default=None, description="Motor shaft speed in RPM")
    rated_motor_current_amps: Optional[float] = Field(default=None, description="Rated motor current in Amps")
    weight_kg: Optional[float] = Field(default=None, description="Weight in kg")
    cooling_medium: Optional[str] = Field(default=None, description="Type of cooling medium")
    pros_and_cons_summary: str = Field(description="Write a 1-sentence summary of the main pros and cons.")

# --- 3. BATCH FILE UPLOADER ---
uploaded_files = st.file_uploader("Upload PDF Datasheets", type=["pdf"], accept_multiple_files=True)

if uploaded_files: # If the user uploaded at least one file
    if st.button("Extract Data from All Files"):
        all_extracted_data = []
        
        # Show a progress bar!
        progress_text = "Processing PDFs..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, uploaded_file in enumerate(uploaded_files):
            # Save temporary file
            temp_pdf_path = f"temp_{uploaded_file.name}"
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            # Send to AI
            gemini_file = client.files.upload(file=temp_pdf_path)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[gemini_file, "Extract the technical specifications. Leave missing specs as null."],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': CompressorSpecs,
                },
            )
            
            # Format Data
            data_dict = json.loads(response.text)
            data_dict["source_file"] = uploaded_file.name
            all_extracted_data.append(data_dict)
            
            os.remove(temp_pdf_path) # Clean up
            
            # Update progress bar
            percent_complete = int(((i + 1) / len(uploaded_files)) * 100)
            my_bar.progress(percent_complete, text=f"Processed {uploaded_file.name}...")

        st.success("Batch Extraction Complete!")
        
        # --- 4. DISPLAY AND DOWNLOAD ---
        df = pd.DataFrame(all_extracted_data)
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Batch CSV", data=csv, file_name="industrial_specs.csv", mime="text/csv")