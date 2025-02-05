import re

entity_unit_map = {
    'width': {'centimetre', 'foot', 'inch', 'metre', 'millimetre', 'yard'},
    'depth': {'centimetre', 'foot', 'inch', 'metre', 'millimetre', 'yard'},
    'height': {'centimetre', 'foot', 'inch', 'metre', 'millimetre', 'yard'},
    'item_weight': {'gram', 'kilogram', 'microgram', 'milligram', 'ounce', 'pound', 'ton'},
    'maximum_weight_recommendation': {'gram', 'kilogram', 'microgram', 'milligram', 'ounce', 'pound', 'ton'},
    'voltage': {'kilovolt', 'millivolt', 'volt'},
    'wattage': {'kilowatt', 'watt'},
    'item_volume': {'centilitre', 'cubic foot', 'cubic inch', 'cup', 'decilitre', 'fluid ounce', 'gallon', 
                    'imperial gallon', 'litre', 'microlitre', 'millilitre', 'pint', 'quart'}
}

allowed_units = {unit for entity in entity_unit_map for unit in entity_unit_map[entity]}

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text).strip()

def extract_value_and_unit(text):
    value_unit_regex = re.compile(r'(\d+\.?\d*)\s*([a-zA-Z]+)')
    match = value_unit_regex.match(text)
    if match:
        return match.groups()  
    return None, None


def map_unit_to_entity(unit):
    for entity, units in entity_unit_map.items():
        if unit in units:
            return entity
    return None


def normalize_unit(unit):
    unit = unit.lower()
    unit_map = {
        'cm': 'centimetre', 'mm': 'millimetre', 'm': 'metre', 'in': 'inch',
        'kg': 'kilogram', 'g': 'gram', 'mg': 'milligram', 'ug': 'microgram',
        'oz': 'ounce', 'lb': 'pound', 't': 'ton', 'v': 'volt', 'w': 'watt',
        'kv': 'kilovolt', 'kw': 'kilowatt', 'l': 'litre', 'ml': 'millilitre'
    }
    return unit_map.get(unit, unit) 

ocr_text_list = ['HEF', 'Glucon-', '9.4in', '23cm']

extracted_entities = []
for token in ocr_text_list:
    cleaned_text = clean_text(token)
    
    value, unit = extract_value_and_unit(cleaned_text)
    
    if value and unit:
        normalized_unit = normalize_unit(unit)
        
        if normalized_unit in allowed_units:
            entity_name = map_unit_to_entity(normalized_unit)
            if entity_name:
                extracted_entities.append((entity_name, value, normalized_unit))

for entity_name, value, unit in extracted_entities:
    print(f"Entity: {entity_name}, Value: {value}, Unit: {unit}")
