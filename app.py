import streamlit as st
from dotenv import load_dotenv
import os
import PyPDF2 as pdf
import google.generativeai as genai
import json
import base64
import re

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error(" Google API key not found in .env file.")
    st.stop()

# LLM Response Function
def generate_response(prompt):
    model = genai.GenerativeModel("gemini-2.5-pro")  # or "gemini-2.5-pro"
    response = model.generate_content(prompt)
    return response.text

# PDF Resume Extraction
def input_pdf_text(uploaded_file):
    if uploaded_file is not None:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    return ""

# Improved Prompt Template
prompt_template = """
You are an experienced ATS (Applicant Tracking System) engineer with deep domain expertise in software engineering, data science, and related tech roles.

Return ONLY valid JSON in this format (no explanation, no markdown):

{{
  "JD Matching Percentage": "XX%",
  "Missing Keywords": ["keyword1", "keyword2"],
  "Profile Summary": "Your summary here",
  "Resume Analysis": "Your detailed analysis here"
}}

Resume:
{text}

Job Description:
{jd}
"""

# JSON Extractor with Fallback
def extract_json_from_response(response_text):
    try:
        # Direct parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Extract inner JSON using regex
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None

# Main Streamlit App

def main():
    st.set_page_config(page_title="ATS Resume Analyzer", layout="centered")
    st.title(" ATS Resume Analyzer")
    st.markdown("Boost your job chances with LLM-powered resume analysis.")

    # VERTICAL layout: JD comes first, then file uploader
    jd = st.text_area(" Job Description", "Paste the job description here...", height=300)
    uploaded_file = st.file_uploader(" Upload Resume (PDF)", type=["pdf"], help="Upload your resume in PDF format.")

    if st.button(" Analyze Resume"):
        if uploaded_file and jd:
            text = input_pdf_text(uploaded_file)
            if text:
                st.info(" Analyzing resume...")
                final_prompt = prompt_template.format(text=text, jd=jd)
                response = generate_response(final_prompt)

                result = extract_json_from_response(response)

                if result:
                    st.subheader(" ATS Analysis Report")
                    st.json(result)

                    # Download link
                    report_str = json.dumps(result, indent=2)
                    b64 = base64.b64encode(report_str.encode()).decode()
                    st.markdown(
                        f'<a href="data:file/json;base64,{b64}" download="ats_report.json"> Download ATS Report</a>',
                        unsafe_allow_html=True
                    )
                else:
                    st.warning(" Could not parse the response as JSON. Here's the raw output:")
                    st.text_area("LLM Output", response, height=300)
            else:
                st.error(" Failed to extract text from PDF.")
        else:
            st.error(" Please upload a resume and enter a job description.")

if __name__ == "__main__":
    main()
