import os
import logging
import pandas as pd
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from langchain_openai.embeddings.azure import AzureOpenAIEmbeddings
from langchain_openai.chat_models.azure import AzureChatOpenAI
import json

class superagent:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
            temperature=0.1,
            azure_endpoint=os.environ["OPENAI_ENDPOINT"],
            openai_api_key=os.environ["OPENAI_KEY"]
        )
        self.embedding = AzureOpenAIEmbeddings(
            openai_api_version=os.environ["AZURE_OPENAI_EMBEDDINGS_API_VERSION"],
            azure_deployment=os.environ["EMBED_MODEL"],
            azure_endpoint=os.environ["OPENAI_ENDPOINT"],
            openai_api_key=os.environ["OPENAI_KEY"]
        )

    def setup_search_client(self, index_name: str) -> SearchClient:
        """
        Creates and returns a SearchClient for a specific index.
        """
        return SearchClient(
            endpoint=os.environ["SEARCH_ENDPOINT"],
            index_name=index_name,
            credential=AzureKeyCredential(os.getenv("SEARCH_KEY"))
        )

    def executeRules(self, rules, index_findoc: str = None) -> pd.DataFrame:
        """
        Get responses from the LLM for all rules and merge them into a DataFrame.
        """
        df = pd.DataFrame(columns=["Review Item", "AI Review Comment"])
        
        for heading, rule in rules.items():
            logging.info(f"Executing {heading} on index {index_findoc}")
            # Initialize the SearchClient with the provided index
            search_client = self.setup_search_client(index_findoc)
            
            # Perform the search query
            search_results = search_client.search(search_text=heading, top=1)
            
            # Extract the relevant information from the search results
            context = "\n".join([result["content"] for result in search_results])
            
            # Split the context into smaller chunks if it exceeds the maximum length
            max_length = 1048576
            chunks = [context[i:i + max_length] for i in range(0, len(context), max_length)]
            
            for chunk in chunks:
                # Format the prompt to include both the context and the rule
                formatted_prompt = f"Context: {chunk}\n\nRule: {rule}"
                
                response = self.llm.invoke(input=[
                    {"role": "system", "content": "You are an AI assistant that helps with financial document analysis. Please provide results in tabular format with columns 1. Review Item (Rule) and 2. AI Review Comment."},
                    {"role": "user", "content": formatted_prompt}
                ])
                
                # Check if the response is empty or not in JSON format
                try:
                    response_content = response.content
                    logging.info(f"Token Usage: {response.response_metadata['token_usage']}")
                    logging.info(f"Response from LLM: {response_content}")
                    if not response_content:
                        raise ValueError("Empty response from LLM")
                    
                    # Parse the tabular response
                    lines = response_content.split("\n")
                    for line in lines[2:]:  # Skip the header lines
                        if line.strip():
                            parts = line.split("|")
                            if len(parts) >= 3:
                                review_item = parts[1].strip()
                                ai_review_comment = parts[2].strip()
                                df.loc[len(df)] = [review_item, ai_review_comment]
                except ValueError as e:
                    logging.error(f"Error parsing response from LLM: {e}")
                    df.loc[len(df)] = [rule, "Invalid response from LLM"]
        
        return df

    def summarize_text(self, text: str) -> str:
        """
        Summarize the given text using the LLM.
        """
        prompt = f"Summarize the following text:\n\n{text}"
        response = self.llm.invoke(input=[
            {"role": "system", "content": "You are an AI assistant that summarizes text."},
            {"role": "user", "content": prompt}
        ])
        
        # Check if the response is empty or not in JSON format
        try:
            response_content = response.content
            logging.info(f"Token Usage: {response.response_metadata['token_usage']}")
            logging.info(f"Response from LLM: {response_content}")
            if not response_content:
                raise ValueError("Empty response from LLM")
            
            # Return the plain text response
            return response_content
        except ValueError as e:
            logging.error(f"Error parsing response from LLM: {e}")
            return "Invalid response from LLM"

    def generate_final_report(self, section_headings: str, review_comments: pd.DataFrame) -> str:
        """
        Generate the final financial summary report based on section headings and review comments.
        """
        prompt = f"Generate a final financial summary report with the following section headings:\n\n{section_headings}\n\nInclude the following discrepancies identified by the Review AI Agent:\n\n{review_comments.to_string(index=False)}"
        response = self.llm.invoke(input=[
            {"role": "system", "content": "You are an AI assistant that generates financial summary reports."},
            {"role": "user", "content": prompt}
        ])
        
        # Check if the response is empty or not in JSON format
        try:
            response_content = response.content
            logging.info(f"Token Usage: {response.response_metadata['token_usage']}")
            logging.info(f"Response from LLM: {response_content}")
            if not response_content:
                raise ValueError("Empty response from LLM")
            
            # Return the plain text response
            return response_content
        except ValueError as e:
            logging.error(f"Error parsing response from LLM: {e}")
            return "Invalid response from LLM"
