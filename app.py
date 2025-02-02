#upload W-2
#extract entities
#save as CSV/xls
#upload to Azure AI search
#query the AI search using llm
#populate the 1040 form
import os
import requests
import json
import logging
import tax_us_w2_analyzer as chunker
#from superagent import superagent  # Import the superagent class
from tax_us_w2_analyzer import analyze_tax_us_w2  # Import the analyze_tax_us_w2 function
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

import pandas as pd
import openpyxl

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastAPI app

app = FastAPI()
@app.post("/uploadfile/")
async def extract_data(file: UploadFile = File(...)):
    try:
        pdf_content = await file.read()
        logger.info("File received")
        
        # Get the JSON output from tax_us_w2_analyzer.py
        w2_json = analyze_tax_us_w2(pdf_content)
        logger.info(f"W2 JSON: {w2_json}")

        # Extract key values from w2_json
        key_values = w2_json

        # Convert to DataFrame
        df = pd.DataFrame([key_values])

        # Save DataFrame to Excel file
        excel_file_path = f"{file.filename}.xlsx"
        df.to_excel(excel_file_path, index=False)
        logger.info(f"Excel file saved at {excel_file_path}")

        # Return JSON response with key values
        return JSONResponse(content={"key_values": key_values})
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
 