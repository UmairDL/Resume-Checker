import time
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import openai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import pandas as pd

# Load environment variables
load_dotenv() 

# Configure the API key for OpenAI GPT
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt4_response(input):
    # Use OpenAI API to generate a response using GPT-4
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Replace with the correct model version if needed
        messages=[
            {"role": "system", "content": "You are a skilled ATS that evaluates resumes."},
            {"role": "user", "content": input}
        ]
    )
    return response.choices[0].message.content # Extract the generated content

def input_pdf_text(uploaded_file):
    # Extract text from the uploaded PDF file
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

# Prompt Template
input_prompt = """
Hey Act Like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of the tech field, software engineering, data science, data analysis,
and big data engineering. Your task is to evaluate the resume based on the given job description.
You must consider that the job market is very competitive, and you should provide 
the best assistance for improving the resumes. Assign the percentage Matching based 
on the Job description (JD) and the missing keywords with high accuracy.

Resume: {text}
Job Description: {jd}

I want the response as per the structure below:
{{"JD Match": "%", 
"MissingKeywords": [], 
"Profile Summary": ""}}
"""

# Gradient Background and Custom CSS for Streamlit
def set_background():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: linear-gradient(to right, #ff7e5f, #feb47b);
            background-attachment: fixed;
            background-size: cover;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Set gradient background
set_background()

# Initial Welcome Page
if "page" not in st.session_state:
    st.session_state.page = "welcome"

if st.session_state.page == "welcome":
    st.title("Welcome to Smart Resume Checker!")
    st.write("This app helps you analyze your resume based on job descriptions or compare multiple resumes.")
    
    # Interactive Spinner on Button Click
    if st.button("Check the Resume"):
        with st.spinner('Wait for it...'):
            time.sleep(2)  # Simulate loading time
        st.success("Done!")
        st.session_state.page = "main"
    
    st.stop()

# Main Page with Two Buttons for Resume Checker and Resume Comparison
if st.session_state.page == "main":
    st.title("Smart Resume Analysis")
    st.text("Select one of the options below:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Resume Checker"):
            st.session_state.page = "resume_checker"
    with col2:
        if st.button("Resume Comparison"):
            st.session_state.page = "resume_comparison"
    st.stop()

# Resume Checker Feature
if st.session_state.page == "resume_checker":
    # Main Menu Button
    if st.button("Main Menu"):
        st.session_state.page = "welcome"
        st.experimental_rerun()  # Return to the landing page
    
    st.title("Resume Checker")
    st.text("Check a single resume for a job description.")
    
    jd = st.text_area("Paste the Job Description")
    uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload a PDF file.")
    
    if st.button("Submit"):
        with st.spinner('Processing...'):
            time.sleep(2)  # Simulate processing time
            if uploaded_file is not None and jd:
                resume_text = input_pdf_text(uploaded_file)
                formatted_prompt = input_prompt.format(text=resume_text, jd=jd)
                response = get_gpt4_response(formatted_prompt)
                
                try:
                    response_data = json.loads(response)
                    jd_match = response_data.get("JD Match", "%")
                    missing_keywords = response_data.get("MissingKeywords", [])
                    profile_summary = response_data.get("Profile Summary", "")
                    
                    st.markdown("**__JD MATCH__**")
                    st.write(jd_match)
                    st.markdown("**__MISSING KEYWORDS__**")
                    st.write(", ".join(missing_keywords) if missing_keywords else "No missing keywords.")
                    st.markdown("**__PROFILE SUMMARY__**")
                    st.write(profile_summary)
                    st.success("Processing complete!")
                except json.JSONDecodeError:
                    st.error("There was an issue with the response format. Please try again.")
            else:
                st.error("Please upload a resume and provide a job description.")

# Resume Comparison Feature
if st.session_state.page == "resume_comparison":
    # Main Menu Button
    if st.button("Main Menu"):
        st.session_state.page = "welcome"
        st.experimental_rerun()  # Return to the landing page
    
    st.title("Resume Comparison")
    st.text("Compare multiple resumes for a given job description.")
    
    jd = st.text_area("Paste the Job Description for comparison")
    uploaded_files = st.file_uploader("Upload Multiple Resumes", type="pdf", accept_multiple_files=True, help="Please upload PDF files.")
    
    if st.button("Submit for Comparison"):
        with st.spinner('Processing...'):
            time.sleep(3)  # Simulate processing time
            if uploaded_files and jd:
                candidates_data = []
                for uploaded_file in uploaded_files:
                    resume_text = input_pdf_text(uploaded_file)
                    formatted_prompt = input_prompt.format(text=resume_text, jd=jd)
                    response = get_gpt4_response(formatted_prompt)
                    
                    try:
                        response_data = json.loads(response)
                        jd_match = response_data.get("JD Match", "N/A")
                        missing_keywords = response_data.get("MissingKeywords", [])
                        profile_summary = response_data.get("Profile Summary", "")
                        
                        candidates_data.append({
                            "File Name": uploaded_file.name,
                            "JD Match": jd_match,
                            "Missing Keywords": ", ".join(missing_keywords) if missing_keywords else "None",
                            "Profile Summary": profile_summary
                        })
                    except json.JSONDecodeError:
                        st.error(f"There was an issue with the response format for {uploaded_file.name}.")
                
                if candidates_data:
                    df = pd.DataFrame(candidates_data)
                    st.subheader("Candidate Comparison")
                    st.dataframe(df)

                    # Plot comparison chart for JD Match percentage
                    try:
                        df['JD Match'] = df['JD Match'].str.replace('%', '').astype(float)
                        st.bar_chart(df.set_index('File Name')['JD Match'])
                    except ValueError:
                        st.error("Unable to plot JD Match as some values are not valid percentages.")
                st.success("Comparison complete!")
            else:
                st.error("Please upload at least one resume and provide a job description.")
