import os
import logging
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from dotenv import load_dotenv,find_dotenv
import json
from openai import AzureOpenAI
import uuid
from azure.search.documents import SearchClient
import logging as logger


filePath = "coca-cola-form10k.pdf"

load_dotenv(find_dotenv(),override=True)
di_end_point = os.getenv("DI_ENDPOINT")
print("di_end_point",di_end_point)
di_key = os.getenv("DI_KEY")
print("di_key",di_key)
openai_endpoint=os.getenv("OPENAI_ENDPOINT")
print("openai_endpoint",openai_endpoint)
openai_key=os.getenv("OPENAI_KEY")
print("openai_key",openai_key)
search_endpoint=os.getenv("SEARCH_ENDPOINT")
print("search_endpoint",search_endpoint)
search_key=os.getenv("SEARCH_KEY")
print("search_key",search_key)
index_name=os.getenv("SEARCH_INDEX_NAME")
print("index_name",index_name)
api_version=os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION")
print("api_version",api_version)
embed_model=os.getenv("EMBED_MODEL")
print("embed_model",embed_model)
ai_search_client=os.getenv("AI_SEARCH_CLIENT")
print("di_end_point",di_end_point)

openai_embedding_client = AzureOpenAI(api_key=openai_key, azure_endpoint=openai_endpoint,
                                          api_version=api_version, azure_deployment=embed_model)
search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=AzureKeyCredential(search_key))

def extract_and_chunk_pdf(pdf_content,di_end_point,di_key,embedding_client,embed_model,ai_search_client):

    try:    
            # with open(filePath,"rb") as f:
            #     pdf_content = f.read()
            document_analysis_client = DocumentAnalysisClient(endpoint=di_end_point, credential=AzureKeyCredential(di_key))
            poller = document_analysis_client.begin_analyze_document("prebuilt-layout", pdf_content)
            result = poller.result()
            document_paragraphs = []
            for para in result.paragraphs:
                document_paragraphs.append({
                    "content": para.content,
                    "role": para.role if hasattr(para, 'role') else None,
                    "bounding_regions": para.bounding_regions if hasattr(para, 'bounding_regions') else None
                })
            print("document_paragraphs",document_paragraphs[1])    
            current_title = None  # Initialize for the current section title
            current_chunk = []    # Initialize to hold content of the current section
            chunks = []  
                            # List to hold all chunk data
            # Counters for statistics
            chunk_count = 0
            prompt_tokens_count = 0
            output_tokens_count = 0
            for para in document_paragraphs:
                content = para["content"]
                role = para.get("role", None)
                # if role=="sectionHeading" : 
                #     print("content.......................",content)
                #     print("role.......................",role)
                if para.get('bounding_regions'):
                    bounding_regions = para['bounding_regions']
                    if len(bounding_regions) > 0 and hasattr(bounding_regions[0], 'pageNumber'):
                        page_number = bounding_regions[0].pageNumber
                if role == "sectionHeading":
                    # Add your code here for handling section headings
                    pass
                    if current_title and current_chunk:
                        chunk_content = " ".join(current_chunk)
                        # Create and store the current chunk before starting a new one
                        print("openai_embedding_client",openai_embedding_client)
                        print("embed_model",embed_model)
                        embedding = create_embeddings(openai_embedding_client, embed_model, chunk_content)
                        chunk_data = {
                            "id": generate_chunk_id(),
                            "filename": filePath,
                            "sectionheading": current_title,
                            "content": chunk_content,
                            "embedding": embedding
                        }
                        chunks.append(chunk_data)
                        # Update counters
                        chunk_count += 1
                        prompt_tokens_count += len(chunk_content.split())
                        output_tokens_count += len(embedding)
                    # Start a new section
                    current_title = content
                    current_chunk = []
                # Append content to the current chunk
                current_chunk.append(content)
                print("current_chunk",current_chunk[0])
            # Finalize the last chunk
            if current_title and current_chunk:
                chunk_content = " ".join(current_chunk)
                embedding = create_embeddings(openai_embedding_client, embed_model, chunk_content)
                chunk_data = {
                    "id": generate_chunk_id(),
                    "filename": filePath,
                    "sectionheading": current_title,
                    "content": chunk_content,
                    "embedding": embedding
                }
                chunks.append(chunk_data)
                # Update counters for the last chunk
                chunk_count += 1
                prompt_tokens_count += len(chunk_content.split())
                output_tokens_count += len(embedding)
            # Upload all chunks to Azure Cognitive Search
            logger.info(f"Uploading {len(chunks)} chunks")
            print("chunks[1]",chunks[1])
            upload_chunks_to_azure_search(chunks, search_client)
            logger.info(f"Successfully uploaded {len(chunks)} chunks to Azure Cognitive Search for file '{filePath}'.")
            # Log summary statistics
            logger.info(f"Summary for file '{filePath}': # of chunks: {chunk_count}, # of prompt tokens: {prompt_tokens_count}, # of output tokens: {output_tokens_count}")
    except Exception as e:
            logger.error(f"Error analyzing PDF '{filePath}': {e}", exc_info=True)

def upload_chunks_to_azure_search(chunks, search_client):
    """
    Uploads chunked data to Azure Cognitive Search.
    Args:
        chunks (list): List of chunk data to upload.
        search_client (SearchClient): Azure Cognitive Search client.
    """
    try:
        result = search_client.upload_documents(documents=chunks)
        logger.info("Chunks successfully uploaded to Azure Cognitive Search.")
        return result
    except Exception as e:
        logger.error(f"Failed to upload chunks to Azure Cognitive Search: {e}")
 
def create_embeddings(openai_embedding_client, embed_model, header):
    """
    Creates embeddings for a given header using OpenAI embeddings.
    Args:
        openai_embedding_client (AzureOpenAI): OpenAI client for embedding creation.
        embed_model (str): The OpenAI embedding model to use.
        header (str): The text content for which embeddings will be generated.
    Returns:
        list: The generated embedding vector.
    """
    try:
        text_embedding = openai_embedding_client.embeddings.create(input=header, model=embed_model)
        embedding_data = json.loads(text_embedding.model_dump_json())["data"][0]['embedding']
        # logger.info(f"Embeddings successfully created for header '{header}'.")
        return embedding_data
    except Exception as e:
        logger.error(f"Failed to create embeddings for header '{header}': {e}")
 
def generate_chunk_id():
    """
    Generates a unique ID for each chunk.
    Returns:
        str: A unique ID string.
    """
    return str(uuid.uuid4())        

def main():
   
    filePath = "C:\FINAI_Contest\coca-cola-form10k.pdf"
    load_dotenv(find_dotenv(),override=True)
    di_end_point = os.getenv("DI_ENDPOINT")
    di_key = os.getenv("DI_KEY")
    openai_endpoint=os.getenv("OPENAI_ENDPOINT")
    openai_key=os.getenv("OPENAI_KEY")
    search_endpoint=os.getenv("SEARCH_ENDPOINT")
    search_key=os.getenv("SEARCH_KEY")
    embedding_client=os.getenv("EMBEDDING_CLIENT")
    embed_model=os.getenv("EMBED_MODEL")
    ai_search_client=os.getenv("AI_SEARCH_CLIENT")
    print("di_end_point",di_end_point)

    extract_and_chunk_pdf(filePath,di_end_point,di_key,embedding_client,embed_model,ai_search_client)
    
if __name__ == "__main__":
    print("vijay here")
    main()
