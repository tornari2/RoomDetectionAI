#!/bin/bash
# Add status endpoint to API Gateway

set -e

API_ID="yady49pjx3"
BLUEPRINTS_RESOURCE_ID="5yuw10"
LAMBDA_ARN="arn:aws:lambda:us-east-2:971422717446:function:room-detection-ai-handler-dev"
REGION="us-east-2"

echo "=========================================="
echo "Creating Status Endpoint in API Gateway"
echo "=========================================="

# Create {blueprint_id} resource under /blueprints
echo "Creating {blueprint_id} resource..."
BLUEPRINT_ID_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id "$API_ID" \
    --parent-id "$BLUEPRINTS_RESOURCE_ID" \
    --path-part "{blueprint_id}" \
    --output json)

BLUEPRINT_ID_RESOURCE_ID=$(echo "$BLUEPRINT_ID_RESOURCE" | jq -r '.id')
echo "✓ Created {blueprint_id} resource: $BLUEPRINT_ID_RESOURCE_ID"

# Create status resource under {blueprint_id}
echo "Creating status resource..."
STATUS_RESOURCE=$(aws apigateway create-resource \
    --rest-api-id "$API_ID" \
    --parent-id "$BLUEPRINT_ID_RESOURCE_ID" \
    --path-part "status" \
    --output json)

STATUS_RESOURCE_ID=$(echo "$STATUS_RESOURCE" | jq -r '.id')
echo "✓ Created status resource: $STATUS_RESOURCE_ID"

# Create GET method
echo "Creating GET method..."
aws apigateway put-method \
    --rest-api-id "$API_ID" \
    --resource-id "$STATUS_RESOURCE_ID" \
    --http-method GET \
    --authorization-type NONE

# Create method integration
echo "Creating Lambda integration..."
aws apigateway put-integration \
    --rest-api-id "$API_ID" \
    --resource-id "$STATUS_RESOURCE_ID" \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations"

# Create OPTIONS method for CORS
echo "Creating OPTIONS method for CORS..."
aws apigateway put-method \
    --rest-api-id "$API_ID" \
    --resource-id "$STATUS_RESOURCE_ID" \
    --http-method OPTIONS \
    --authorization-type NONE

aws apigateway put-integration \
    --rest-api-id "$API_ID" \
    --resource-id "$STATUS_RESOURCE_ID" \
    --http-method OPTIONS \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations"

# Add Lambda permission for new resource
echo "Adding Lambda permission..."
aws lambda add-permission \
    --function-name room-detection-ai-handler-dev \
    --statement-id apigateway-status-$(date +%s) \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:971422717446:${API_ID}/*/*" \
    2>/dev/null || echo "  (Permission may already exist)"

# Deploy the changes
echo ""
echo "Deploying changes..."
aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name dev \
    --description "Added status endpoint"

echo ""
echo "=========================================="
echo "✓ Status Endpoint Created Successfully!"
echo "=========================================="
echo ""
echo "Endpoint: /api/v1/blueprints/{blueprint_id}/status"
echo "Try uploading a photo again - it should work now!"
echo "=========================================="

