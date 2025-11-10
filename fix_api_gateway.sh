#!/bin/bash
# Quick fix to add binary media types to API Gateway

set -e

echo "=========================================="
echo "Adding Binary Media Types to API Gateway"
echo "=========================================="

# Get API ID from AWS
API_NAME="room-detection-ai-api-dev"

echo "Looking for API Gateway: $API_NAME"
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='${API_NAME}'].id" --output text)

if [ -z "$API_ID" ]; then
    echo "❌ Error: Could not find API Gateway with name: $API_NAME"
    echo "Available APIs:"
    aws apigateway get-rest-apis --query "items[*].[name,id]" --output table
    exit 1
fi

echo "✓ Found API Gateway: $API_ID"
echo ""

# Add binary media types
echo "Adding binary media types..."

# Add multipart/form-data
echo "  - multipart/form-data"
aws apigateway update-rest-api \
    --rest-api-id "$API_ID" \
    --patch-operations \
        op=add,path=/binaryMediaTypes/multipart~1form-data || true

# Add image/png  
echo "  - image/png"
aws apigateway update-rest-api \
    --rest-api-id "$API_ID" \
    --patch-operations \
        op=add,path=/binaryMediaTypes/image~1png || true

# Add image/jpeg
echo "  - image/jpeg"
aws apigateway update-rest-api \
    --rest-api-id "$API_ID" \
    --patch-operations \
        op=add,path=/binaryMediaTypes/image~1jpeg || true

# Add */*
echo "  - */*"
aws apigateway update-rest-api \
    --rest-api-id "$API_ID" \
    --patch-operations \
        op=add,path=/binaryMediaTypes/*~1* || true

echo ""
echo "✓ Binary media types added!"
echo ""

# Get current stage name
STAGE_NAME="dev"

echo "Creating new deployment..."
aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE_NAME" \
    --description "Added binary media types for file upload support"

echo ""
echo "=========================================="
echo "✓ API Gateway Updated Successfully!"
echo "=========================================="
echo ""
echo "The API Gateway will now:"
echo "  - Treat multipart/form-data as binary"
echo "  - Base64 encode the request body"
echo "  - Set isBase64Encoded=true in Lambda event"
echo ""
echo "Try uploading a photo now - it should work!"
echo "=========================================="

