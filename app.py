from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os
import requests
import json
import logging
import extract_and_chunk_pdf as chunker
from superagent import superagent  # Import the superagent class

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def setup():
    super_agent = superagent()
    return super_agent

super_agent = setup()

app = FastAPI()

di_end_point = os.getenv("DI_ENDPOINT")
di_key = os.getenv("DI_KEY")
openai_endpoint = os.getenv("OPENAI_ENDPOINT")
openai_key = os.getenv("OPENAI_KEY")
search_endpoint = os.getenv("SEARCH_ENDPOINT")
search_key = os.getenv("SEARCH_KEY")
embedding_client = os.getenv("EMBEDDING_CLIENT")
embed_model = os.getenv("EMBED_MODEL")
ai_search_client = os.getenv("AI_SEARCH_CLIENT")
SEARCH_INDEX_NAME = "azuresearchvij-index"

class TextInput(BaseModel):
    text: str

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        pdf_content = await file.read()
        logger.info("File received")
        # Extract sections based on rules from JSON
        with open("rules.json", "r") as f:
            rules = json.load(f)
            print("rules......................", rules)

        df = super_agent.executeRules(rules, "azuresearchvij-index")
        response = df.to_dict(orient="records")
        logger.info(f"Response: {response}")
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/summary/")
async def summarize_text(input: TextInput):
    try:
        summary = super_agent.summarize_text(input.text)
        return JSONResponse(content={"summary": summary})
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/finalreport/")
async def generate_final_report(input: TextInput):
    try:
        # Get the review comments from the Review AI Agent
        with open("rules.json", "r") as f:
            rules = json.load(f)
        review_comments_df = super_agent.executeRules(rules, "azuresearchvij-index")
        
        # Generate the final report
        final_report = super_agent.generate_final_report(input.text, review_comments_df)
        return JSONResponse(content={"final_report": final_report})
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
