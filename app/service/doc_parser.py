
import os
from PyPDF2 import PdfReader

def extract_text_from_pdf(file : str):
    """
    Extract text from PDF
    """
    
    reader = PdfReader(file)
    text=""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return {
        "text" : text.strip()
        
    }
    

def extract_text_from_txt(file :str):
    """
    Extract text from a txt file

    """
    with open(file, "r", encoding="utf-8") as f:
        text = f.read()
        
        return {
            "text" : text.strip(),
            "page_count" : 1,
            "word_count" : str(len(text.split()))
        }
    


def extract_text(file_path :str) :
    """"
    Extract text from a document file

        
        Args file_path (str) : The Path to the document file.
    """
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".txt" :
        return extract_text_from_txt(file_path)
    else :
        raise ValueError("Unsupported file type. Only PDF and TXT files are allowed")
    
    
    
