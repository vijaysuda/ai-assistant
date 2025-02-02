import os
from dotenv import load_dotenv
import base64
from azure.core.credentials import AzureKeyCredential
# from azure.ai.formrecognizer import DocumentAnalysisClient

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult

load_dotenv()  # Load environment variables from .env file

def format_address_value(address_value):
    return f"\n......House/building number: {address_value.house_number}\n......Road: {address_value.road}\n......City: {address_value.city}\n......State: {address_value.state}\n......Postal code: {address_value.postal_code}"

def analyze_tax_us_w2(pdf_content: str) -> dict:
    endpoint = os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCUMENTINTELLIGENCE_API_KEY"]
    path_to_sample_document = "W2.pdf"
    
    document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # with open(path_to_sample_document, "rb") as f:
    #     poller = document_analysis_client.begin_analyze_document(
    #         model_id="prebuilt-tax.us.w2", document=f.read(), locale="en-US"
    #     )
    # w2s = poller.result()
    
   
    analyze_request = {
            "base64Source": base64.b64encode(pdf_content).decode("utf-8")
        }
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-tax.us.w2", 
         body=analyze_request,
         output_content_format="markdown"
    )
    result: AnalyzeResult = poller.result()
    print(result.content)
    w2s: AnalyzeResult = poller.result()
    output = {}
    if w2s.documents:
        for idx, w2 in enumerate(w2s.documents):
            print(f"--------Analyzing US Tax W-2 Form #{idx + 1}--------")
            if w2.fields:
                form_variant = w2.fields.get("W2FormVariant")
                if form_variant:
                    output["Form_variant"]=form_variant.get('valueString')
                    print(
                        f"Form_variant: {form_variant.get('valueString')} has confidence: " 
                        f"{form_variant.confidence}"
                    )
                tax_year = w2.fields.get("TaxYear")
                if tax_year:
                    output["Tax_year"]=tax_year.get('valueString')
                    print(f"Tax_year: {tax_year.get('valueString')} has confidence: {tax_year.confidence}")
                w2_copy = w2.fields.get("W2Copy")
                if w2_copy:
                    output["w2_copy"]=w2_copy.get('valueString')
                    print(f"W-2 Copy: {w2_copy.get('valueString')} has confidence: {w2_copy.confidence}")
                employee = w2.fields.get("Employee")
                if employee:
                    print("Employee data:")
                    employee_name = employee.get("valueObject").get("Name")
                    if employee_name:
                        output["employee_name"]=employee_name.get('valueString')
                        print(f"...Name: {employee_name.get('valueString')} has confidence: {employee_name.confidence}")
                wages_tips = w2.fields.get("WagesTipsAndOtherCompensation")
                if wages_tips:
                    output["wages_tips"]=wages_tips.get('valueNumber')
                    print(
                        f"Wages, tips, and other compensation: {wages_tips.get('valueNumber')} "
                        f"has confidence: {wages_tips.confidence}"
                    )

                        
    # output = {}
    # if w2s.documents:
    #     for idx, w2 in enumerate(w2s.documents):
    #         if w2.fields:
    #             form_variant = w2.fields.get("W2FormVariant")
    #             if form_variant:
    #                 output["Form variant"] = form_variant.value
    #                 print(f"Form variant: {form_variant.value}")
    #             tax_year = w2.fields.get("TaxYear")
    #             if tax_year:
    #                 output["Tax year"] = tax_year.value
    #                 print(f"Tax year: {tax_year.value}")
    #             w2_copy = w2.fields.get("W2Copy")
    #             if w2_copy:
    #                 output["W-2 Copy"] = w2_copy.value
    #                 print(f"W-2 Copy: {w2_copy.value}")
    #             employee_name = w2.fields.get("Employee's name,address, and ZIP code")
    #             if employee_name:
    #                 output["Employee Name"] = employee_name.value
    #                 print(f"Employee Name: {employee_name.value}")
    #             Social_security_wages = w2.fields.get("Social security wages")  
    #             if Social_security_wages:
    #                 output["Social security wages"] = Social_security_wages.value
    #                 print(f"Social security wages: {Social_security_wages.value}")  
    return output

if __name__ == "__main__":
    print(analyze_tax_us_w2())