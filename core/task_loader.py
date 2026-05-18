import json
import os
import glob
import random
from core.state_manager import state_manager

def validate_task(data):
    """
    Validate a task JSON dictionary against the official Jinglu Robot schema.
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
    common_fields = ["task_title", "speech_start", "speech_end"]
    
    for stage in five_e_stages:
        stage_data = data[stage]
        if not isinstance(stage_data, dict):
            print(f"Validation Error: Stage '{stage}' must be an object (dictionary).")
            return False
            
        for field in common_fields:
            if field not in stage_data:
                print(f"Validation Error: Stage '{stage}' is missing standard field '{field}'.")
                return False
                
        # Only require generic description on non-interactive stages
        if stage in ["engage", "explore", "explain"] and "description" not in stage_data:
            print(f"Validation Error: Stage '{stage}' is missing standard field 'description'.")
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

def load_all_tasks(directory_path="Tasks/task_jsons"):
    """
    Scans the given directory for .json files, loads, and validates them using load_task().
    Returns a list of explicitly valid task dictionaries.
    """
    valid_tasks = []
    
    # Resolve path relative to the project root
    if not os.path.isabs(directory_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        directory_path = os.path.join(project_root, directory_path)
        
    if not os.path.exists(directory_path):
        print(f"Warning: Task directory '{directory_path}' does not exist.")
        return valid_tasks
        
    pattern = os.path.join(directory_path, "*.json")
    json_files = glob.glob(pattern)
    
    for filepath in json_files:
        task_data = load_task(filepath)
        if task_data is not None:
            valid_tasks.append(task_data)
            
    print(f"Successfully loaded and validated {len(valid_tasks)} tasks from {directory_path}.")
    return valid_tasks

# Cache for loaded tasks
_loaded_tasks = None

def get_loaded_tasks():
    global _loaded_tasks
    if _loaded_tasks is None:
        _loaded_tasks = load_all_tasks()
    return _loaded_tasks

def pick_random_task(exclude_ids=None):
    """
    Selects a random task from the loaded pool, avoiding any task_ids in exclude_ids.
    Stores the picked task into state_manager.current_task and returns it.
    """
    if exclude_ids is None:
        exclude_ids = []
        
    all_tasks = get_loaded_tasks()
    available_tasks = [t for t in all_tasks if t.get("task_id") not in exclude_ids]
    
    if not available_tasks:
        print("Warning: No available tasks to pick from (all excluded or none loaded).")
        return None
        
    picked_task = random.choice(available_tasks)
    print(f"Picked random task: '{picked_task.get('task_name')}' (ID: {picked_task.get('task_id')})") 
    
    # Store in state manager
    state_manager.set_current_task(picked_task)
    
    return picked_task

def build_task_queue(exclude_ids=None):
    """
    Builds an ordered queue of all available tasks sorted sequentially by task_id
    (t_1, t_2, t_3, ...). Tasks are served one by one in this fixed order.
    """
    if exclude_ids is None:
        exclude_ids = []
    
    all_tasks = get_loaded_tasks()
    available = [t for t in all_tasks if t.get("task_id") not in exclude_ids]
    
    if not available:
        print("[TaskLoader] Warning: No tasks available for queue!")
        return []
    
    # Sort by task_id numerically (t_1 < t_2 < t_3 ...)
    available.sort(key=lambda t: int(t.get("task_id", "t_0").split("_")[-1]))
    
    print(f"[TaskLoader] Built sequential task queue: {[t.get('task_id') for t in available]}")
    return available
