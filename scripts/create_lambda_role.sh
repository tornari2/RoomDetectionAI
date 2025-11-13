#!/bin/bash
# Create Lambda execution role with necessary permissions

set -e

ROLE_NAME="Lambda-room-detection-execution-role"
POLICY_NAME="Lambda-room-detection-policy"

echo "Creating Lambda execution role..."

# Create trust policy for Lambda
cat > /tmp/lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  2>&1 | grep -v "EntityAlreadyExists" || echo "Role already exists"

# Create policy document
cat > /tmp/lambda-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::room-detection-ai-blueprints-dev/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:InvokeEndpoint"
      ],
      "Resource": "arn:aws:sagemaker:us-east-2:971422717446:endpoint/room-detection-yolov8-endpoint"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/lambda-policy.json

# Attach basic Lambda execution policy (for CloudWatch logs)
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  2>&1 | grep -v "EntityAlreadyExists" || echo "Policy already attached"

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)

echo "✅ Lambda role created: $ROLE_ARN"
echo ""
echo "Role ARN: $ROLE_ARN"
echo ""
echo "Update lambda-config.json with this role ARN"

