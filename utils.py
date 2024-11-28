import easyocr
from datetime import datetime
from passporteye import read_mrz
import re

reader = easyocr.Reader(['en', 'ms'])  # You can add other languages if needed

# Validation functions
def is_alpha(value):
    return re.fullmatch(r'[A-Z]+', value) is not None

def is_alphanumeric(value):
    return re.fullmatch(r'[A-Z0-9]+', value) is not None

def is_digit(value):
    return re.fullmatch(r'[0-9]+', value) is not None

def is_alpha_with_spaces(value):
    return re.fullmatch(r'[A-Z ]+', value) is not None

# Function to clean up extra 'K's from OCR errors
def clean_ocr_errors(value):
    # Remove standalone 'K' and any trailing 'K's, as well as excess spaces
    value = re.sub(r'\bK\b', '', value)      # Remove standalone 'K'
    value = re.sub(r'K+\s*$', '', value)     # Remove trailing 'K's at the end
    value = re.sub(r'\s+K+\s+', ' ', value)  # Remove isolated 'K's in between
    return re.sub(r'\s+', ' ', value).strip()  # Remove multiple spaces and trim

# Refinement function
def refine_document_data(data):
    keys_to_keep = {'type', 'country', 'number', 'date_of_birth', 'expiration_date', 'nationality', 'sex', 'names', 'surname'}
    refined_data = {}
    for key, value in data.items():
        if key not in keys_to_keep:
            continue
        if key == 'type' and not is_alpha(value):
            refined_data[key] = ''.join(filter(str.isalpha, value))  # Keep only alphabets
        elif key == 'country' and not is_alpha(value):
            refined_data[key] = ''.join(filter(str.isalpha, value))  # Keep only alphabets
        elif key == 'number' and not is_alphanumeric(value):
            refined_data[key] = ''.join(filter(str.isalnum, value))  # Keep only alphanumeric
        elif key == 'date_of_birth' and not is_digit(value):
            refined_data[key] = ''.join(filter(str.isdigit, value))  # Keep only digits
        elif key == 'expiration_date' and not is_digit(value):
            refined_data[key] = ''.join(filter(str.isdigit, value))  # Keep only digits
        elif key == 'nationality' and not is_alpha(value):
            refined_data[key] = ''.join(filter(str.isalpha, value))  # Keep only alphabets
        elif key == 'sex' and not is_alpha(value):
            refined_data[key] = ''.join(filter(str.isalpha, value))  # Keep only alphabets
        elif key == 'names' and not is_alpha_with_spaces(value):
            value = ''.join(filter(lambda x: x.isalpha() or x.isspace(), value))  # Keep alphabets and spaces
            refined_data[key] = clean_ocr_errors(value)  # Clean OCR errors
        elif key == 'surname' and not is_alpha_with_spaces(value):
            value = ''.join(filter(lambda x: x.isalpha() or x.isspace(), value))  # Keep alphabets and spaces
            refined_data[key] = clean_ocr_errors(value)  # Clean OCR errors
        elif key == 'personal_number' and not is_digit(value):
            refined_data[key] = ''.join(filter(str.isdigit, value))  # Keep only digits
        else:
            refined_data[key] = value  # If valid, keep the original value
    refined_data['expiration_date'] = convert_date(refined_data['expiration_date'])
    refined_data['date_of_birth'] = convert_date(refined_data['date_of_birth'])
    refined_data['names'] = refined_data['names'].split("   ")[0].split("  ")[0]
    return refined_data

def convert_date(date_str):
    if len(date_str) == 6 and is_digit(date_str):
        # Assuming dates follow YYMMDD format; convert to YYYY-MM-DD
        year = int(date_str[:2])
        year += 2000 if year < 30 else 1900  # Handling century (assuming YY < 50 means 2000s, otherwise 1900s)
        return datetime(year, int(date_str[2:4]), int(date_str[4:6])).strftime('%Y-%m-%d')
    return date_str  # Return original if not in expected format

def extract_mrz_data(image_path):
    # Read the MRZ from the image
    mrz = read_mrz(image_path)

    # Check if MRZ data was found
    if mrz is None:
        print("No MRZ data found.")
        return None

    # Parse the MRZ data
    mrz_data = mrz.to_dict()

    return mrz_data


def get_passport_info(passport):
    return refine_document_data(extract_mrz_data(passport))
