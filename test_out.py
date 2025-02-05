# Importing necessary modules and libraries
import src.constants as constants  # Importing constants for unit mappings
import src.utils as utils  # Utility functions for downloading images
import os  # File system operations
import pandas as pd  # For handling the dataset (CSV file)
from paddleocr import PaddleOCR  # OCR library for extracting text from images
import re  # Regular expressions for text processing
import spacy  # NLP library for Named Entity Recognition (NER)
import os  # Needed for environment settings and path management

# Set an environment variable to avoid issues with some libraries
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Constants used for entity-to-unit mapping
entity_unit_map = constants.entity_unit_map
allowed_units = constants.allowed_units

# Load the small English model for NER
nlp = spacy.load('en_core_web_sm')

# Function to clean text by removing punctuation and extra spaces
# Input: raw text
# Output: cleaned text (without special characters)
def clean_text(text):
    return re.sub(r'[^\w\s]', '', text).strip()

# Function to extract numeric values and units from a given text
# Input: text (string)
# Output: numeric value and unit as a tuple (value, unit) if found, else (None, None)
def extract_value_and_unit(text):
    value_unit_regex = re.compile(r'(\d+\.?\d*)\s*([a-zA-Z]+)')
    match = value_unit_regex.match(text)
    if match:
        return match.groups()  # Returns (value, unit)
    return None, None  # If no match found

# Function to map units to specific entities (like weight, volume, etc.)
# Input: unit (string)
# Output: corresponding entity if the unit is valid, else None
def map_unit_to_entity(unit):
    for entity, units in entity_unit_map.items():
        if unit in units:
            return entity
    return None

# Function to normalize units into a standard format (e.g., 'cm' -> 'centimetre')
# Input: raw unit (string)
# Output: normalized unit (string)
def normalize_unit(unit):
    unit = unit.lower()  # Convert to lowercase
    unit_map = {
        'cm': 'centimetre', 'mm': 'millimetre', 'm': 'metre', 'in': 'inch',
        'kg': 'kilogram', 'g': 'gram', 'mg': 'milligram', 'ug': 'microgram',
        'oz': 'ounce', 'lb': 'pound', 't': 'ton', 'v': 'volt', 'w': 'watt',
        'kv': 'kilovolt', 'kw': 'kilowatt', 'l': 'litre', 'ml': 'millilitre'
    }
    return unit_map.get(unit, unit)  # Return normalized unit or the original one

# Function to apply Named Entity Recognition (NER) on the input text
# Input: text (string)
# Output: list of detected entities (each as a tuple of text, entity label)
def apply_ner(text):
    doc = nlp(text)  # Process the text with Spacy NLP
    entities = [(ent.text, ent.label_) for ent in doc.ents]  # Extract entities
    return entities

# Path configurations for the dataset and image storage
dataset_path = "dataset"
cwd = os.getcwd()  # Get the current working directory
image_path = os.path.join(cwd, "Image")  # Path to store downloaded images
if not os.path.exists(image_path):
    os.makedirs(image_path)  # Create the image directory if it doesn't exist

dataset_path = os.path.join(cwd, dataset_path)  # Path to the dataset folder
train = os.path.join(dataset_path, "train.csv")  # Path to the training CSV file
df = pd.read_csv(train)  # Load the dataset into a DataFrame

# Extract a list of image URLs from the dataset (first 100 images)
img_path = df["image_link"].tolist()[:100]

# Download images using utility function
for img_url in img_path:
    utils.download_image(img_url, image_path)

# Get the local file paths for all the downloaded images
images_path = [os.path.join(image_path, os.path.basename(url)) for url in img_path]

# Initialize the OCR model with English language and angle classification
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Dictionary to store OCR results
output_dic = {}

# Loop through each image and perform OCR to extract text
for i, image in enumerate(images_path):
    result = ocr.ocr(image, cls=True)  # Perform OCR on the image
    detected_texts = [word_info[1][0] if word_info is not None and len(word_info) > 1 and len(word_info[1]) > 0 else '' 
                  for line in result if line is not None for word_info in line]

    output_dic[df['image_link'][i]] = detected_texts  # Save extracted text

# List to store extracted entities (Entity Name, Value, Unit)
extracted_entities = []

# Process the detected texts from OCR
for detected_texts in output_dic.values():
    for text in detected_texts:
        cleaned_text = clean_text(text)  # Clean the OCR output text

        # Apply NER to extract entities from the cleaned text
        ner_entities = apply_ner(cleaned_text)
        for entity_text, entity_type in ner_entities:
            # Extract the numeric value and unit from the entity
            value, unit = extract_value_and_unit(entity_text)
            if value and unit:
                # Normalize the unit and check if it's allowed
                normalized_unit = normalize_unit(unit)
                if normalized_unit in allowed_units:
                    # Map the unit to a specific entity (like weight, volume)
                    entity_name = map_unit_to_entity(normalized_unit)
                    if entity_name:
                        extracted_entities.append((entity_name, value, normalized_unit))  # Save the extracted entity

# Create a DataFrame to store the extracted entities
output_df = pd.DataFrame(extracted_entities, columns=['Entity Name', 'Value', 'Unit'])

# Add an index column to the DataFrame
output_df['index'] = range(len(output_df))

# Create a new 'Prediction' column with the format 'Value Unit'
output_df['prediction'] = output_df.apply(lambda row: f"{row['Value']} {row['Unit']}", axis=1)

# Rearrange columns to match the desired format (index, prediction)
output_df = output_df[['index', 'prediction']]

# Save the final output to a CSV file
output_df.to_csv('test_out.csv', index=False)
