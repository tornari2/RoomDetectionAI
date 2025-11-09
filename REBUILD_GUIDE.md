# When Do You Need to Rebuild?

## ✅ Endpoint Creation: ONE TIME ONLY

**This is the ONLY time you create the endpoint.** Once it's `InService`, it stays running until you delete it.

## 🔄 Docker Image Rebuilds: Only When Code Changes

With our optimized Dockerfile, rebuilds are FAST:

### Code Changes Only (`inference.py`)
- **Rebuild time:** ~30 seconds (only rebuilds last 2 layers)
- **Why:** Dependencies are cached, only code layer rebuilds
- **Command:** `./scripts/build_with_codebuild.sh`

### Dependency Changes (`requirements.inference.txt`)
- **Rebuild time:** ~2-3 minutes
- **Why:** Pip install layer rebuilds, but base image cached
- **Command:** `./scripts/build_with_codebuild.sh`

### Dockerfile Changes
- **Rebuild time:** ~8-12 minutes (full rebuild)
- **Why:** Base image or structure changed
- **Command:** `./scripts/build_with_codebuild.sh`

## 🔄 Endpoint Updates: Only When Deploying New Image

You only need to update the endpoint when you want to deploy a new Docker image:

1. **Build new image:** `./scripts/build_with_codebuild.sh`
2. **Update endpoint:** `./scripts/check_build_and_deploy.sh`

**Update time:** ~5-10 minutes (endpoint deletion + creation)

## 📊 Typical Workflow

### First Time (What You're Doing Now)
1. ✅ Build Docker image (~8-12 minutes) - DONE
2. ✅ Create endpoint (~5-10 minutes) - IN PROGRESS
3. ✅ Test endpoint

### Future Code Changes
1. Edit `inference.py`
2. Run `./scripts/build_with_codebuild.sh` (~30 seconds)
3. Run `./scripts/check_build_and_deploy.sh` (~5-10 minutes)
4. Test

### No Changes Needed
- **Endpoint stays running** - no action needed
- **Just invoke it** via Lambda or directly

## 💡 Key Points

- ✅ **Endpoint creation:** ONE TIME ONLY (what you're doing now)
- ✅ **Code changes:** FAST rebuilds (~30 seconds) thanks to layer caching
- ✅ **No changes:** Endpoint keeps running, no rebuild needed
- ✅ **All builds:** Run on CodeBuild (AWS), not your Mac

## 🚀 Quick Commands

```bash
# Check build status
./scripts/check_build_status.sh

# Build new image (when code changes)
./scripts/build_with_codebuild.sh

# Deploy after build completes
./scripts/check_build_and_deploy.sh

# Check endpoint status
aws sagemaker describe-endpoint --endpoint-name room-detection-yolov8-endpoint --region us-east-2
```

