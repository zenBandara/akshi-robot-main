import json
import os

def validate_task(data):
    """
    Validate a task JSON dictionary against the official Akshi Robot schema.
    Returns True if valid, False if invalid. Prints detailed error messages.
    """
    if not isinstance(data, dict):
        print("Validation Error: Task data is not a JSON object.")
        return False

    # 1. Check Root Keys
    root_keys = ["task_id", "task_name", "description", "engage", "explore", "explain", "elaborate", "evaluate"]
    for key in root_keys:
        if key not in data:
            print(f"Validation Error: Missing root key '{key}'")
            return False
            
    # 2. Check 5E Standard Fields
    five_e_stages = ["engage", "explore", "explain", "elaborate", "evaluate"]
    standard_fields = ["task_title", "speech_start", "speech_end", "description"]
    
    for stage in five_e_stages:
        stage_data = data[stage]
        if not isinstance(stage_data, dict):
            print(f"Validation Error: Stage '{stage}' must be an object (dictionary).")
            return False
            
        for field in standard_fields:
            if field not in stage_data:
                print(f"Validation Error: Stage '{stage}' is missing standard field '{field}'.")
                return False
                
    # 3. Check Interactive Fields (elaborate & evaluate)
    interactive_stages = ["elaborate", "evaluate"]
    interactive_fields = ["task_type", "task_description", "multiple_choices_word", "multiple_choices_images", "correct_option"]
    
    for stage in interactive_stages:
        stage_data = data[stage]
        for field in interactive_fields:
            if field not in stage_data:
                print(f"Validation Error: Interactive stage '{stage}' is missing required field '{field}'.")
                return False
                
        # Validate options definitions
        mc_words = stage_data["multiple_choices_word"]
        mc_images = stage_data["multiple_choices_images"]
        
        if not isinstance(mc_words, dict) or not isinstance(mc_images, dict):
             print(f"Validation Error: '{stage}' multiple choices must be dictionaries.")
             return False
             
        for op in ["op1", "op2", "op3", "op4"]:
            if op not in mc_words:
                print(f"Validation Error: '{stage}.multiple_choices_word' is missing '{op}'.")
                return False
            if op not in mc_images:
                print(f"Validation Error: '{stage}.multiple_choices_images' is missing '{op}'.")
                return False
                
    return True

def load_task(filepath):
    """
    Read and parse a single JSON task file.
    Returns the parsed dictionary if valid, or None if validation fails.
    """
    if not os.path.exists(filepath):
        print(f"Error: Task file not found at '{filepath}'.")
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if validate_task(data):
            return data
        else:
            print(f"Failed to load task from '{filepath}' due to validation errors.")
            return None
            
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error in '{filepath}': {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading '{filepath}': {e}")
        return None
