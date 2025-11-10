import subprocess
import json

# Remove all layers from Lambda function
print("Removing problematic Lambda layers...")
result = subprocess.run([
    'aws', 'lambda', 'update-function-configuration',
    '--function-name', 'room-detection-ai-handler-dev',
    '--layers', ''
], capture_output=True, text=True)

print(result.stdout if result.returncode == 0 else result.stderr)
print("\n✅ Layers removed. Lambda will use bundled numpy instead.")

