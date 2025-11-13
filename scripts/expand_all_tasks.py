#!/usr/bin/env python3
"""
Expand all tasks in tasks.json using Taskmaster's expansion functionality.
This script directly calls the Taskmaster expansion logic.
"""

import json
import sys
import os
from pathlib import Path

# Add taskmaster to path if needed
sys.path.insert(0, str(Path(__file__).parent))

def expand_all_tasks(tasks_file_path, use_research=True):
    """Expand all pending tasks into subtasks."""
    
    # Load tasks
    with open(tasks_file_path, 'r') as f:
        data = json.load(f)
    
    tasks = data['tags']['master']['tasks']
    pending_tasks = [t for t in tasks if t.get('status') == 'pending' and 
                     ('subtasks' not in t or len(t.get('subtasks', [])) == 0)]
    
    print(f"Found {len(pending_tasks)} tasks to expand")
    print(f"Total tasks: {len(tasks)}")
    print()
    
    if not pending_tasks:
        print("No tasks need expansion (all have subtasks or are not pending)")
        return
    
    # Try to use taskmaster CLI via subprocess
    import subprocess
    
    expanded_count = 0
    for task in pending_tasks:
        task_id = task['id']
        print(f"Expanding task {task_id}: {task['title']}")
        
        try:
            # Use npx to run task-master-ai expand
            result = subprocess.run(
                ['npx', '-y', 'task-master-ai', 'expand', 
                 '--id', str(task_id),
                 '--research' if use_research else '',
                 '--file', tasks_file_path],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=Path(tasks_file_path).parent.parent.parent
            )
            
            if result.returncode == 0:
                print(f"  ✓ Task {task_id} expanded successfully")
                expanded_count += 1
            else:
                print(f"  ✗ Task {task_id} failed: {result.stderr[:200]}")
                
        except Exception as e:
            print(f"  ✗ Task {task_id} error: {str(e)[:200]}")
    
    print(f"\n✓ Expanded {expanded_count}/{len(pending_tasks)} tasks")

if __name__ == "__main__":
    tasks_file = ".taskmaster/tasks/tasks.json"
    if not os.path.exists(tasks_file):
        print(f"Error: {tasks_file} not found")
        sys.exit(1)
    
    expand_all_tasks(tasks_file, use_research=True)

