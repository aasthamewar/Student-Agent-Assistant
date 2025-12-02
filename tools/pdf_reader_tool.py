
from google import genai

client = genai.Client()

def pdf_reader_tool(file_path: str) -> str:
    """
    Uploads a PDF file to Google Generative AI and generates a summary.
    
    Args:
        file_path: Path to the PDF file to upload
        
    Returns:
        The generated summary text
    """
    print("Uploading PDF...")
    pdf_file = client.files.upload(file=file_path)
    print(f"File uploaded successfully: {pdf_file.name}")
    
    response = client.models.generate_content(
        model="gemini-2.5-pro",  # Use Pro for better document understanding
        contents=[
            pdf_file,
            "Summarize this document and tell me the main conclusion.",
        ]
    )
    
    result = response.text
    
    # Clean up the uploaded file
    client.files.delete(name=pdf_file.name)
    print(f"File deleted: {pdf_file.name}")
    
    return result