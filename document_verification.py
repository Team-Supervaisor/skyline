import streamlit as st
import pdfplumber # type: ignore
from openai import OpenAI # type: ignore
from pdf2image import convert_from_bytes # type: ignore
import os
import easyocr # type: ignore

api_key = os.getenv("OPENAI_API_KEY")
reader = easyocr.Reader(['en'])

def extract_text_from_scanned_pdf(uploaded_file):
    if uploaded_file is None:
        st.warning("No file uploaded. Please upload a valid PDF.")
        return None  
    pdf_bytes = uploaded_file.read()
    images = convert_from_bytes(pdf_bytes,
                                poppler_path=r"Release-24.08.0-0\poppler-24.08.0\Library\bin")
    extracted_text = "\n".join([" ".join(reader.readtext(image, detail=0)) for image in images])
    return extracted_text

def extract_text_from_pdf(pdf_path, chunk_size=10):
    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(0, len(pdf.pages), chunk_size):
            chunk_text = "\n".join([pdf.pages[j].extract_text() for j in range(i, min(i+chunk_size, len(pdf.pages))) if pdf.pages[j].extract_text()])
            text_chunks.append(chunk_text)
    return text_chunks

def summarize_text(text_chunks, client):
    summarized_rules = []
    for chunk in text_chunks:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Summarize this text."}]
        )
        summarized_rules.append(response.choices[0].message.content)
    return summarized_rules

def document_verification_app():
    st.markdown('# RERA Document Verification')

    if st.sidebar.button("🏠 Home"):
        st.session_state["page"] = "home"
        st.rerun()

    if api_key:
        client = OpenAI(api_key=api_key)  # Create client once
        rera_rules_pdf = "ReraRules2017.pdf"

        if "rera_summary" not in st.session_state:
            st.session_state["rera_summary"] = summarize_text(extract_text_from_pdf(rera_rules_pdf), client)
            st.success("RERA rules summarized and stored in memory.")
        elif "rera_summary" in st.session_state:
            st.success("RERA rules already stored in memory.")

    # Step 1: File Upload
    uploaded_file = st.file_uploader("Upload a document for compliance checking", type=["pdf"])

    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file  # Store file in session state immediately
        st.success("File uploaded successfully!")

    if st.session_state.uploaded_file:
        extracted_text = extract_text_from_scanned_pdf(uploaded_file)
        if st.button("Run General Compliance Check"):
            st.write("### General Compliance Check")
            st.write("Comparing document against RERA rules...")

            prompt_1 = f"""
            RERA Rules: {st.session_state.get('rera_summary', 'No rules found')}
            
            Considering the RERA rules and acts, and general best practice for document verification, 
            identify the potential issues with the following document related to it's format, completeness, and compliance 
            with standard legal requirements and create a table summarising it.
            
            Document:
            {extracted_text}
    
            Present the output in a tabular format with the following columns:
            - Issue Type
            - Brief Explanation
            - Probability of Issue (1-10)
            """

            response_1 = client.chat.completions.create(
                model='gpt-4o', temperature=0.0, max_tokens=2000, messages=[{"role": "user", "content": prompt_1}]
            )

            st.write(response_1.choices[0].message.content)

        # Step 2: Specific Section Analysis
        text_input_search = st.text_input("Specify what to analyze (e.g., page numbers, escrow account, signatures, etc.)")

        if st.button('Analyze Specific Section'):
            prompt_2 = f"""
            RERA Rules: {st.session_state.get('rera_summary', 'No rules found')}
            
            Document:
            {extracted_text}
            
            Based on the RERA rules above, analyze the document given above based on the following search parameters:
            {text_input_search}
            
            Check for discrepancies, lack of clarity, missing information, etc. Give a very short but detailed report of
            any issues you find relating specifically to the search parameter.
    
            """

            response_2 = client.chat.completions.create(
                model='gpt-4o', temperature=0.0, max_tokens=2000, messages=[{"role": "user", "content": prompt_2}]
            )

            st.write(response_2.choices[0].message.content)
