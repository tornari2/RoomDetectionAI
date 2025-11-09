# CodeBuild Solution for Docker Manifest Format Issue

## Recommended Solution: AWS CodeBuild

**Why CodeBuild?**
- ✅ **Runs on Linux** - Docker images will be in Docker v2 format (not OCI)
- ✅ **Fully Managed** - No infrastructure to maintain
- ✅ **Seamless ECR Integration** - Built-in Docker support
- ✅ **Cost-Effective** - Pay only for build time (~$0.005/minute)
- ✅ **Repeatable** - Can be triggered via script or CI/CD
- ✅ **Fast** - Builds typically complete in 5-10 minutes

## Quick Start

### Option 1: Use the Automated Script (Recommended)

```bash
cd /Users/michaeltornaritis/Desktop/WK4_RoomDetectionAI
./scripts/build_with_codebuild.sh
```

This script will:
1. Create a source zip with `sagemaker/` directory and `buildspec.yml`
2. Upload to S3
3. Create CodeBuild project (if needed)
4. Start the build
5. Provide monitoring commands

### Option 2: Manual Steps

1. **Create CodeBuild project:**
   ```bash
   python3 scripts/setup_codebuild.py --create-project-only
   ```

2. **Create source zip:**
   ```bash
   cd /Users/michaeltornaritis/Desktop/WK4_RoomDetectionAI
   zip -r /tmp/source.zip sagemaker/ buildspec.yml -x '*.git*' '*.pyc' '__pycache__/*'
   ```

3. **Upload to S3:**
   ```bash
   aws s3 cp /tmp/source.zip s3://room-detection-ai-blueprints-dev/codebuild/source.zip
   ```

4. **Start build:**
   ```bash
   aws codebuild start-build --project-name room-detection-docker-build --region us-east-2
   ```

5. **Monitor build:**
   ```bash
   aws codebuild batch-get-builds --ids <build-id> --region us-east-2
   ```

6. **Once build completes, deploy:**
   ```bash
   python3 sagemaker/scripts/deploy_model.py
   ```

## Files Created

- `buildspec.yml` - CodeBuild build specification
- `scripts/setup_codebuild.py` - CodeBuild project setup script
- `scripts/build_with_codebuild.sh` - Automated build script

## Cost Estimate

- **Build time:** ~5-10 minutes
- **Cost:** ~$0.025 - $0.05 per build
- **Storage:** S3 storage for source zip (~10 MB) - negligible cost

## Alternative Solutions (Not Recommended)

### Option 2: EC2 Instance
- ❌ Requires managing EC2 instance
- ❌ More expensive (~$0.01/hour even when idle)
- ❌ More setup complexity

### Option 3: Local Linux VM
- ❌ Requires Docker Desktop or VM setup
- ❌ Platform-specific issues
- ❌ Not repeatable across team members

## Next Steps After Build

Once CodeBuild successfully builds and pushes the image:

1. **Verify image format:**
   ```bash
   aws ecr describe-images --repository-name room-detection-yolov8 --region us-east-2
   ```

2. **Deploy model:**
   ```bash
   python3 sagemaker/scripts/deploy_model.py
   ```

3. **Test inference:**
   ```bash
   python3 sagemaker/tests/test_inference.py --endpoint-name room-detection-yolov8-endpoint --image <path-to-test-image>
   ```

## Troubleshooting

If CodeBuild fails:
- Check CloudWatch logs for the build
- Verify IAM permissions for CodeBuild role
- Ensure ECR repository exists and is accessible
- Check that `buildspec.yml` is in the root of the source zip

