import streamlit as st
import requests
import pandas as pd
from io import BytesIO

# Set the title of the Streamlit app
st.title("Tax document AI Assistant")

# Create a sidebar with menu options
menu = ["W2-form", "Invoice Agent", "AI chat Agent", "Tax filing review Agent"]
choice = st.sidebar.selectbox("Select Menu", menu)

# PDF Upload and Processing
if choice == "W2-form":
    st.header("W2-form Excel export Agent")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        if st.button("Submit"):
            files = {"file": uploaded_file.getvalue()}
            print("got files")
            with st.spinner("Processing..."):
                response = requests.post("http://127.0.0.1:8000/uploadfile/", files=files)
                print("response...", response)
                if response.status_code == 200:
                    response_json = response.json()
                    print("response_json...", response_json)
                    st.write("W2 JSON:")
                    w2_json = response_json.get("key_values", {})
                    print("w2_json...............", w2_json)
                    if w2_json:
                        st.table([{"Key": key, "Value": value} for key, value in w2_json.items()])
                        
                        # Convert the JSON data to a DataFrame
                        df = pd.DataFrame([w2_json])
                        
                        # Create a BytesIO buffer to write the Excel file
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Sheet1')
                        output.seek(0)
                        
                        # Create a download button
                        st.download_button(
                            label="Export to Excel",
                            data=output.getvalue(),
                            file_name="w2_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.write("No W2 JSON data found.")
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
    rai_filters = """
        The following RAI (Responsible AI) filters are configured in Azure AI studio to prevent inappropriate content and ensure ethical use of AI:
        
        1. Hate
        2. Violence
        3. Discrimination
    """
    st.write(rai_filters)

# Final Report AI Agent
elif choice == "Final Report AI Agent":
    st.header("Final Report AI Agent")
    summary_text = st.text_area("Enter text for final report")

    if st.button("Generate Final Report"):
        with st.spinner("Generating Final Report..."):
            response = requests.post("http://127.0.0.1:8000/finalreport/", json={"text": summary_text})
            if response.status_code == 200:
                final_report = response.json().get("final_report", "No final report found")
                st.write(f"Final Report: {final_report}")
            else:
                st.write("Error:", response.json())