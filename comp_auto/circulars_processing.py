from transformers import pipeline, BartForConditionalGeneration, BartTokenizer
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import fitz
import re,pickle

def convert_pdf_to_images(pdf_path):
    try:
        doc=fitz.open(pdf_path)
        images=[]
        for page_num in range(doc.page_count):
            page=doc[page_num]
            image=page.get_pixmap()
            img = Image.frombytes("RGB", (image.width, image.height), image.samples)
            images.append(img)
        return images
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []
    finally:
        if doc:
            doc.close()

def extracted_text_from_img(image_path):
    img=None
    try:
       img=Image.open(image_path)
       text=pytesseract.image_to_string(img)
       return text
    except Exception as e:
       print(f"Error extracting text from image: {e}")
       return ""
    finally:
        if img:
            img.close()

def split_passages(text, min_length=20):
    lines = text.split('\n')

    audit_points = []
    current_point = ""

    for line in lines:
        if re.match(r'^(\d+\.|\([ivxlcdm]+\))\s*(.*)', line):
           if current_point:
              audit_points.append(current_point.strip())
           current_point = line
        else:
            # If not a new audit point, append to the current one
            current_point += '\n' + line

    # Add the last audit point
    if current_point:
        audit_points.append(current_point.strip())

    return audit_points

# def load_model_and_tokenizer(file_path):
#     with open(file_path, 'rb') as model_file:
#          model, tokenizer = pickle.load(model_file)
#     return model, tokenizer

# def summarize(text, model, tokenizer):
#     summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
#     summary = summarizer(text, max_length=150, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)[0]['summary_text']
#     return summary
