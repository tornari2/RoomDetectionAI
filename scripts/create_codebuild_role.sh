#!/bin/bash
# Create CodeBuild service role with proper permissions

set -e

ROLE_NAME="CodeBuild-room-detection-role"
POLICY_NAME="CodeBuild-room-detection-policy"

echo "Creating CodeBuild service role..."

# Create trust policy for CodeBuild
cat > /tmp/codebuild-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file:///tmp/codebuild-trust-policy.json \
  2>&1 | grep -v "EntityAlreadyExists" || echo "Role already exists"

# Create policy document
cat > /tmp/codebuild-policy.json <<EOF
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
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:us-east-2:971422717446:repository/room-detection-yolov8"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::room-detection-ai-blueprints-dev/codebuild/*"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/codebuild-policy.json

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)

echo "✅ CodeBuild role created: $ROLE_ARN"
echo ""
echo "Role ARN: $ROLE_ARN"
echo ""
echo "Now create CodeBuild project with:"
echo "  aws codebuild create-project --service-role $ROLE_ARN ..."

