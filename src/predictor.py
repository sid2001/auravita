import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
import os
import shutil
import cv2
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Path to your Tesseract executable (change this accordingly)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'


# %%
def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF using PyPDF2.
    
    Args:
    pdf_path (str): Path to the input PDF file.
    
    Returns:
    str: Extracted text from the PDF.
    """
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

# %%
def extract_text_from_image(image_path):
    """
    Extracts text from an image using Tesseract OCR.
    
    Args:
    image_path (str): Path to the input image file.
    
    Returns:
    str: Extracted text from the image.
    """
    with Image.open(image_path) as img:
        text = pytesseract.image_to_string(img)
    return text

# %%
def extract_text_from_folder(folder_path):
    """
    Extracts text from all files (images and PDFs) in a folder.
    
    Args:
    folder_path (str): Path to the folder containing image and/or PDF files.
    
    Returns:
    dict: A dictionary mapping file names to extracted text.
    """
    extracted_texts = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            text = extract_text_from_image(file_path)
            extracted_texts[filename] = text
        elif filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
            extracted_texts[filename] = text
    return extracted_texts

# %%
keyword_lists = {
    'lab_record': [
        "assessment report",
        "assessment",
        "test administered",
        "test finding:",
        "end of the report",
        "report",
        "sample collected",
        "test Name",
        "clinical significance",
        "correlate with clinical condition",
        "correlated clinically",
        "collection date",
        "sample receive date",
        "sample type",
        "bio. ref interval",
        "unit",
        "result",
        "biochemistry",
        "biological reference interval",
        "result(s)",
        "report",
        "laboratory test report",
        "test parameter",
        "test results",
        "lab findings",
        "lab tests",
        "diagnosis information",
        "imaging sciences",
        "x ray",
        "x-ray",
        "measures",
        "is normal",
        "observed",
        "noted"
    ],
    'doctor_prescription': [
        "RX",
        "1 - 0 - 0",
        "0 - 1 - 0",
        "0 - 0 - 1",
        "1 . 1 . 2",
        "1 - x - x",
        "x - x - 1",
        "x - 1 - x"
        "patient prescription",
        "medication prescribed",
        "dosage instructions",
        "medication details",
        "prescription details",
        "prescription",
        "hospital",
        "apollo"
    ],
    'medical_bill': [
        "bill",
        "op bill",
        "gross amount",
        "payment amount",
        "mrp",
        "gst%",
        "payment",
        "amount",
        "cash",
        "upi",
        "debit card, credit card",
        "rs",
        "total amount due",
        "payment method",
        "invoice number",
        #"BILL",
        "bill"
    ],
    'discharge_summary': [
        "Discharge summary",
        "Out - patient - record",
        "IP summary",
        "Patient Discharge Details",
        "Post-Discharge Instructions",
        "Discharge Medications",
        "discharge"
    ]
}


# %%
def score_based_search(extracted_text, keyword_lists):
    """
    Performs a score-based search using keyword lists on the extracted text.
    
    Args:
    extracted_text (str): Text extracted from the image.
    keyword_lists (dict): A dictionary containing keyword lists for different categories.
    
    Returns:
    dict: A dictionary containing scores for each category.
    """
    scores = {category: 0 for category in keyword_lists.keys()}

    scores['doctor_prescription']=1
    
    # Convert the extracted text to lowercase for case-insensitive matching
    extracted_text_lower = extracted_text.lower()
    
    # Iterate through each category and its corresponding keyword list
    for category, keywords in keyword_lists.items():
        for keyword in keywords:
            # Check if the keyword exists in the extracted text
            if keyword.lower() in extracted_text_lower:
                # Increment the score for the corresponding category
                scores[category] += 1
    
    print(scores)
    return scores

# %%
def move_file_to_category_folder(filename, category):
    """
    Moves the file to a folder based on the specified category.
    
    Args:
    filename (str): Name of the file.
    category (str): Category with the highest score.
    """
    category_folder = os.path.join("./sorted_docs", category)
    # Check if the category folder exists, if not, create it
    if not os.path.exists(category_folder):
        os.makedirs(category_folder)
    # Move the file to the category folder
    src_path = os.path.join("./images", filename)
    dst_path = os.path.join(category_folder, filename)
    shutil.move(src_path, dst_path)

def date_wise_pescription_sorting():
    directories = {
        "doctor_prescription": os.path.join("./sorted_docs", "doctor_prescription"),
        "lab_record": os.path.join("./sorted_docs", "lab_record")
    }
    for name, path in directories.items():
        directory = path
        for filename in os.listdir(directory):
            fname = os.path.join(directory, filename)
            # checking if it is a file
            if os.path.isfile(fname) and '.jpeg' in fname:
                #filename
                print(fname)
                img = cv2.imread(fname)
                #pyt.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
                text = pytesseract.image_to_string(img)
                #print(text)

                with open("/home/sisa/mediaura/src/sample_data/output.txt","w+") as f:
                    f.write(text)
                    f.close()

                f=open("/home/sisa/mediaura/src/sample_data/output.txt","r+")
                for line in f.readlines():
                    if re.findall(r"\d{2}\s+[a-zA-Z]{3}\s+\d{4}",line):
                        print((re.findall(r"\d{2}\s+[a-zA-Z]{3}\s+\d{4}",line))[0])
                        date=(re.findall(r"\d{2}\s+[a-zA-Z]{3}\s+\d{4}",line))[0].replace(" ","-")
                        months=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                        for i in months:
                            if i in date:
                                date=date.replace(i,str((months.index(i))+1))
                        nwname=directory+"\\"+date+".jpeg"
                        os.rename(fname,nwname)
                        break
                    elif re.findall(r"\d{2}-[a-zA-Z]{3}-\d{4}",line):
                        print((re.findall(r"\d{2}-[a-zA-Z]{3}-\d{4}",line))[0])
                        nwname=directory+"\\"+(re.findall(r"\d{2}-[a-zA-Z]{3}-\d{4}",line))[0]+'.jpeg'
                        months=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                        for i in months:
                            if i in date:
                                date=date.replace(i,str((months.index(i))+1))
                        nwname=directory+"\\"+date+".jpeg"
                        os.rename(fname,nwname)
                        break
                    elif re.findall(r"\d{2}/\d{2}/\d{4}",line):
                        print((re.findall(r"\d{2}/\d{2}/\d{4}",line))[0])
                        if '/' in (re.findall(r"\d{2}/\d{2}/\d{4}",line))[0]:
                            date=(re.findall(r"\d{2}/\d{2}/\d{4}",line))[0].replace('/','-')
                            # import pdb;pdb.set_trace()
                            date=date.split("-")
                            if '0' in date[1]:
                                date[1]=date[1][1]
                            date="-".join(date)	
                            nwname= directory+"\\"+date+'.jpeg'
                            os.rename(fname,nwname)
                        break

# %%
# Example usage
#folder_path = './images'  # Path to your folder containing image and/or PDF files
#extracted_texts = extract_text_from_folder(folder_path)
#i=0
#for filename, text in extracted_texts.items():
#    i=i+1
#    scores = score_based_search(text, keyword_lists) 
#    highest_score_category = max(scores, key=scores.get)
#    print(f"Category with highest score: {highest_score_category}")
#    move_file_to_category_folder(filename, highest_score_category)
#    print(f"file count sorted : {i}")
#
# %%
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin, you should restrict this to specific origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Only image and PDF files are supported")


    # Get the file path
    upload_dir = './images'
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_texts = extract_text_from_folder(upload_dir)
    for filename, text in extracted_texts.items():
        scores = score_based_search(text, keyword_lists)
        highest_score_category = max(scores, key=scores.get)
        move_file_to_category_folder(filename, highest_score_category)
        date_wise_pescription_sorting()

    return {"message": "File uploaded and sorted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

# %%
