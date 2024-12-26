import streamlit as st
import requests
import os

st.image("C:\\FINAI_Contest\\ai-copilot\\banner-AIContest.png", use_container_width=True)
# Set the title of the Streamlit app
st.title("Tax Document Uploader and Analyzer")

# Create a sidebar with menu options
menu = ["Review AI Agent", "Summary AI Agent", "RAI AI Agent", "Final Report AI Agent"]
choice = st.sidebar.selectbox("Select Menu", menu)

# PDF Upload and Processing
if choice == "Review AI Agent":
    st.header("Review AI Agent")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        if st.button("Submit"):
            files = {"file": uploaded_file.getvalue()}
            pdf_link = "https://investors.coca-colacompany.com/filings-reports/annual-filings-10-k/content/0001104659-24-035312/0001104659-24-035312.pdf"
            print("got files")
            with st.spinner("Processing..."):
                response = requests.post("http://127.0.0.1:8000/uploadfile/", files=files)
                if response.status_code == 200:
                    response_json = response.json()
                    for item in response_json:
                        st.write(f"Review Item: {item.get('Review Item', 'N/A')}")
                        st.write(f"[AI Review Comment]({pdf_link}): {item.get('AI Review Comment', 'N/A')}")
                        st.write("---")
                else:
                    st.write("Error:", response.json())

# Summary AI Agent
elif choice == "Summary AI Agent":
    st.header("Summary AI Agent")
    summary_text = st.text_area("Enter text for summary")

    if st.button("Get Summary"):
        with st.spinner("Generating summary..."):
            response = requests.post("http://127.0.0.1:8000/summary/", json={"text": summary_text})
            if response.status_code == 200:
                summary = response.json().get("summary", "No summary found")
                st.write(f"Summary: {summary}")
            else:
                st.write("Error:", response.json())

# RAI AI Agent
elif choice == "RAI AI Agent":
    st.header("RAI AI Agent")
    st.image("C:\\FINAI_Contest\\ai-copilot\RAI_Image.png", use_container_width=True)
    rai_filters = """
        The following RAI (Responsible AI) filters are configured in Azure AI studio  to prevent inappropriate content and ensure ethical use of AI:
        
        1. Hate
        2. Violence
        3. Discrimination
        4. Sexual Harassment
        5. Fraud
        6. Cyber Security
        7. Bribery
        8. Corruption
        9. Conflict of Interest
        10. Ethical Violations
        11. Other
        """
    st.markdown(rai_filters)

# Final Report AI Agent
elif choice == "Final Report AI Agent":
    st.header("Final Report AI Agent")
    summary_text = st.text_area("Enter topics (section headings) for Final report")

    if st.button("Generate Final Report"):
        with st.spinner("Generating Final Report..."):
            response = requests.post("http://127.0.0.1:8000/finalreport/", json={"text": summary_text})
            if response.status_code == 200:
                final_report = response.json().get("final_report", "No final report found")
                st.write(f"Final Report: {final_report}")
            else:
                st.write("Error:", response.json())
