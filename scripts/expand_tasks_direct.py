#!/usr/bin/env python3
"""
Expand all tasks into subtasks using GPT-4-32k directly.
This bypasses the MCP/CLI issues and directly generates subtasks.
"""

import json
import os
import sys
from pathlib import Path
from openai import OpenAI

# Load config to get model settings
config_path = Path('.taskmaster/config.json')
with open(config_path) as f:
    config = json.load(f)

main_model = config['models']['main']
model_name = main_model['modelId']
# Map deprecated model names to current ones
if model_name == 'gpt-4-32k':
    model_name = 'gpt-4-turbo-preview'  # 128k context, similar to old 32k
elif model_name == 'gpt-4':
    model_name = 'gpt-4-turbo-preview'
max_tokens = min(main_model.get('maxTokens', 64000), 4000)  # Cap at 4000 for completion tokens
temperature = main_model.get('temperature', 0.2)

print(f"Using model: {model_name}")
print(f"Max tokens: {max_tokens}, Temperature: {temperature}")
print()

# Get API key from environment or MCP config
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    # Try to read from global MCP config
    try:
        mcp_config_path = Path.home() / '.cursor' / 'mcp.json'
        with open(mcp_config_path) as f:
            mcp_config = json.load(f)
            api_key = mcp_config.get('mcpServers', {}).get('taskmaster-ai', {}).get('env', {}).get('OPENAI_API_KEY')
    except:
        pass

if not api_key:
    print("Error: OPENAI_API_KEY not found")
    print("Please set it in environment or .cursor/mcp.json")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# Load tasks
tasks_file = Path('.taskmaster/tasks/tasks.json')
with open(tasks_file) as f:
    data = json.load(f)

tasks = data['tags']['master']['tasks']
pending_tasks = [t for t in tasks if t.get('status') == 'pending' and 
                 ('subtasks' not in t or len(t.get('subtasks', [])) == 0)]

print(f"Found {len(pending_tasks)} tasks to expand\n")

def generate_subtasks(task, client, model_name, max_tokens, temperature):
    """Generate subtasks for a given task using GPT-4."""
    
    prompt = f"""You are a project management assistant. Break down the following task into 5-8 specific, actionable subtasks.

Task ID: {task['id']}
Title: {task['title']}
Description: {task['description']}
Details: {task.get('details', '')}
Priority: {task.get('priority', 'medium')}
Dependencies: {task.get('dependencies', [])}

Generate subtasks that are:
1. Specific and actionable
2. Properly ordered (respecting dependencies)
3. Each subtask should be completable independently
4. Include implementation details when relevant

Return ONLY a JSON array of subtasks, each with:
- id: sequential number (1, 2, 3...)
- title: brief, descriptive title
- description: concise description
- status: "pending"
- details: implementation details (optional)

Example format:
[
  {{
    "id": 1,
    "title": "Subtask title",
    "description": "Subtask description",
    "status": "pending",
    "details": "Implementation details"
  }}
]"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful project management assistant that breaks down tasks into actionable subtasks. Always return valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        subtasks = json.loads(content)
        return subtasks
        
    except Exception as e:
        print(f"  Error generating subtasks: {e}")
        return []

# Expand each task
expanded_count = 0
for task in pending_tasks:
    task_id = task['id']
    print(f"Expanding task {task_id}: {task['title']}")
    
    subtasks = generate_subtasks(task, client, model_name, max_tokens, temperature)
    
    if subtasks:
        task['subtasks'] = subtasks
        print(f"  ✓ Created {len(subtasks)} subtasks")
        expanded_count += 1
    else:
        print(f"  ✗ Failed to generate subtasks")
    print()

# Save updated tasks
with open(tasks_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✓ Expanded {expanded_count}/{len(pending_tasks)} tasks")
print(f"✓ Saved to {tasks_file}")

