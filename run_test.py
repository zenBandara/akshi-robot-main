import sys
sys.path.append('.')
import core.task_loader as task_loader
tasks = task_loader.get_loaded_tasks()
print(f"Loaded {len(tasks)} tasks.")
