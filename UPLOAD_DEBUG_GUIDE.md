# Image Upload Debugging Guide

## Problem
Photo uploads were failing with error: "File does not appear to be a valid PNG or JPG image"

## Root Cause
The multipart form data parser was not correctly extracting the file content from the HTTP request body, leading to:
1. Extra bytes being included before/after the actual image data
2. Incorrect file signature detection
3. Poor error messages making debugging difficult

## Solutions Implemented

### 1. **Robust Multipart Parsing**
- Uses Python's built-in `email` library as the primary parser
- Falls back to custom boundary-based parsing if email library fails
- Handles both base64-encoded and raw body formats from API Gateway

### 2. **Comprehensive Debugging Logging**
The Lambda handler now logs:
- Request details (body type, length, encoding)
- Content-Type header
- Body preview (hex and text)
- Boundary extraction
- Each multipart part found
- File signature verification at multiple stages
- Detailed validation results

### 3. **Improved Body Handling**
- Detects if body is base64 encoded (even if `isBase64Encoded` flag is incorrect)
- Handles multipart data in both string and byte formats
- Validates body is not empty before processing

### 4. **Better Error Messages**
- Shows actual hex signature received vs. expected
- Provides helpful error messages indicating next steps
- Distinguishes between different failure modes

## How to Debug Upload Issues

### 1. **Check CloudWatch Logs**
After upload attempt, look for:
```
Upload request received
  isBase64Encoded: true/false
  body type: <class 'str'> or <class 'bytes'>
  body length: XXXXX bytes
  Content-Type: multipart/form-data; boundary=...
```

### 2. **Verify Body Preview**
Look for:
```
Body preview (first XXX bytes):
  Hex: 2d2d2d2d... (should start with 2d2d for "--" boundary marker)
  Text (safe): ------WebKitFormBoundary...
```

### 3. **Check Boundary Parsing**
```
  Boundary string: ----WebKitFormBoundaryXXXXXX
  Looking for boundary: b'------WebKitFormBoundaryXXXXXX'
  Found X parts after splitting by boundary
```

### 4. **Verify File Extraction**
```
  Part X: Found file part!
    Content-Type: image/png
    Raw file content: XXXXX bytes
    First 20 bytes (hex): 89504e470d0a1a0a... (PNG) or ffd8ffe0... (JPEG)
```

### 5. **Check File Validation**
```
Validating file:
  Content-Type: image/png
  File size: XXXXX bytes
  First 4 bytes (hex): 89504e47 (PNG) or ffd8ffe0 (JPEG)
  PNG check: True/False
  JPEG check: True/False
```

## Common Issues and Fixes

### Issue 1: "No file found in multipart request"
**Cause:** Parser couldn't extract file from multipart data
**Fix:** Check that the form field name is "file" (not "image" or "upload")
**Debug:** Look for "Content-Disposition: form-data; name="file"" in logs

### Issue 2: "Invalid file signature"
**Cause:** File content has extra bytes or is corrupted
**Fix:** Check the "First 20 bytes (hex)" output in logs
- PNG should start with: `89504e47`
- JPEG should start with: `ffd8ffe0` or `ffd8ffe1`

If you see different bytes at the start, the file extraction is including extra data.

### Issue 3: "Expected multipart/form-data"
**Cause:** Content-Type header is missing or incorrect
**Fix:** Ensure frontend sends proper multipart/form-data with boundary

## Testing Locally

To test the Lambda function locally with a sample image:

```python
import json
import base64

# Read your test image
with open('test_image.png', 'rb') as f:
    image_bytes = f.read()

# Create multipart body
boundary = 'TestBoundary12345'
body = (
    f'------{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    f'Content-Type: image/png\r\n\r\n'
).encode('utf-8') + image_bytes + f'\r\n------{boundary}--\r\n'.encode('utf-8')

# Create test event
event = {
    'httpMethod': 'POST',
    'path': '/api/v1/blueprints/upload',
    'headers': {
        'Content-Type': f'multipart/form-data; boundary=----{boundary}'
    },
    'body': base64.b64encode(body).decode('utf-8'),
    'isBase64Encoded': True
}

# Test the handler
from handler import lambda_handler
result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
```

## Next Steps if Still Failing

1. **Copy the exact CloudWatch logs** showing the upload attempt
2. **Check the "First 20 bytes (hex)" output** - this will show what's actually being extracted
3. **Verify the file works** - try opening it locally to ensure it's not corrupted
4. **Test with different image** - try both PNG and JPEG files
5. **Check API Gateway configuration** - ensure binary media types are configured correctly

## Files Modified
- `/lambda/handler.py` - Updated `parse_multipart_form_data()`, `validate_file()`, and `handle_upload()` functions

## Deployment
After modifying the handler, redeploy the Lambda function:
```bash
cd lambda
./deploy.py
```

Or update via AWS Console/CLI.

