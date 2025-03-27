import streamlit as st
from openai import OpenAI # type: ignore
import pdfplumber # type: ignore
#from serpapi import GoogleSearch # type: ignore
import serpapi

import os
#import pytesseract
from pdf2image import convert_from_path # type: ignore
from dotenv import load_dotenv # type: ignore
import os
import easyocr # type: ignore

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
reader = easyocr.Reader(["en"])

def extract_text_from_pdfs(pdf_files):
    extracted_texts = []
    for pdf_file in pdf_files:
        with pdfplumber.open(pdf_file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            extracted_texts.append(text)
    return "\n".join(extracted_texts)

def extract_text_with_ocr(pdf_file):
    images = convert_from_path(pdf_file, poppler_path=r"Release-24.08.0-0\poppler-24.08.0\Library\bin")
    text = "\n".join([" ".join(reader.readtext(img, detail=0)) for img in images])  # OCR
    return text

def search_case_details(case_title):
    params = {
        "q": case_title + " RERA real estate legal case", 
        "api_key": SERPAPI_KEY,
        "num": 3,  # Limit results
    }
    search =  serpapi.search(params)
    #search = serpapi.GoogleSearch(params)
    results = search.get_dict()

    if "organic_results" in results:
        return [
            {"title": res["title"], "link": res["link"], "snippet": res["snippet"]}
            for res in results["organic_results"][:3]  # Return top 3 results
        ]

    return []

def process_uploaded_files(files):
    if not files:
        return "No evidence provided."

    filenames = [file.name for file in files]
    return f"Uploaded evidence files: {', '.join(filenames)}"

def analyze_case(consumer_statement, builder_statement, consumer_evidence, builder_evidence, case_title=None):
    reference_cases = []

    if case_title:
        reference_cases = search_case_details(case_title)  # Fetch details from SerpAPI

    example_format_1 = extract_text_with_ocr("OrderExample1.pdf")
    example_format_2 = extract_text_with_ocr("OrderExample2.pdf")

    system = f"""You are a RERA executive in Haryana, and have to take a look at consumer complaint, builder's statement,
        consumer statement and supporting documents(any quotes from other orders, written agreements, project plans)
        On the basis of these things, you need to write an order, or give an adjournment with valid reasons."""

    prompt = f"""
        The following is the standard format used in RERA legal orders:

        Example Order Format:
        {example_format_1[:2000]} 
        {example_format_2[:2000]}
        
        Case Analysis:
        - Consumer's Statement:** {consumer_statement}
        - Consumer's Evidence:** {consumer_evidence}

        - Builder's Statement:** {builder_statement}
        - Builder's Evidence:** {builder_evidence}
        
        - Past Similar Cases: {reference_cases if reference_cases else "No past case references provided."}

        Refer to the information given above to reach a verdict for the case. Refer to the evidence used and call
        attention to the reference case when they are provided. Ensure your verdict is drawn from the similar
        circumstances of the reference case and refer to it correctly, using proper legal language and following the
        Order Format shown to you above.
        
        Print only the "Order" section, in the example order format and ensure that details about the order are included.
        """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def case_analysis_app():
   st.title("Mock Case Verdict System")

   if st.sidebar.button("🏠 Home"):
       st.session_state["page"] = "home"
       st.rerun()

   st.subheader("Statements")
   consumer_statement = st.text_area("Enter Consumer Statement")
   builder_statement = st.text_area("Enter Builder Statement")

   st.subheader("Upload Evidence")
   consumer_evidence_files = st.file_uploader("Upload evidence files for Consumer", accept_multiple_files=True, type=["pdf", "png", "jpg"])
   builder_evidence_files = st.file_uploader("Upload evidence files for Builder", accept_multiple_files=True, type=["pdf", "png", "jpg"])

   st.subheader("Search for Reference Cases")
   case_title = st.text_input("Enter the title of a past case to search for")

   if st.button("Get Verdict"):
       if not consumer_statement or not builder_statement:
           st.warning("Both parties must provide a statement!")
       else:
           consumer_evidence_text = process_uploaded_files(consumer_evidence_files)
           builder_evidence_text = process_uploaded_files(builder_evidence_files)

           verdict = analyze_case(
               consumer_statement, builder_statement, consumer_evidence_text, builder_evidence_text, case_title
           )
           st.subheader("Verdict")
           st.write(verdict)
