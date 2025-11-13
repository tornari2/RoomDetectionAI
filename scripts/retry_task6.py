#!/usr/bin/env python3
"""Retry expanding task 6"""

import json
from pathlib import Path
from openai import OpenAI

# Get API key
mcp_config_path = Path.home() / '.cursor' / 'mcp.json'
with open(mcp_config_path) as f:
    mcp_config = json.load(f)
    api_key = mcp_config.get('mcpServers', {}).get('taskmaster-ai', {}).get('env', {}).get('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

# Load tasks
with open('.taskmaster/tasks/tasks.json') as f:
    data = json.load(f)

task = [t for t in data['tags']['master']['tasks'] if t['id'] == 6][0]

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

Return valid JSON only, no markdown formatting."""

response = client.chat.completions.create(
    model='gpt-4-turbo-preview',
    messages=[
        {'role': 'system', 'content': 'You are a helpful project management assistant. Return ONLY valid JSON arrays, no markdown, no code blocks.'},
        {'role': 'user', 'content': prompt}
    ],
    max_tokens=4000,
    temperature=0.2
)

content = response.choices[0].message.content.strip()
# Clean up any markdown
if '```json' in content:
    content = content.split('```json')[1].split('```')[0].strip()
elif '```' in content:
    content = content.split('```')[1].split('```')[0].strip()

try:
    subtasks = json.loads(content)
    task['subtasks'] = subtasks
    
    # Save
    with open('.taskmaster/tasks/tasks.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f'✓ Task 6 expanded with {len(subtasks)} subtasks')
except json.JSONDecodeError as e:
    print(f'✗ JSON parse error: {e}')
    print(f'Response content: {content[:500]}')

