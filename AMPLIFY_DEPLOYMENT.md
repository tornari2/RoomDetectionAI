# AWS Amplify Frontend Deployment Guide

## Prerequisites
- AWS Account with Amplify access
- GitHub repository with the code
- API Gateway endpoint URL

## Step 1: Prepare the Repository

The repository is already configured with:
- ✅ `amplify.yml` - Build configuration
- ✅ Vite build setup in `frontend/package.json`
- ✅ Environment variable support for API URL

## Step 2: Deploy to AWS Amplify

### Option A: AWS Amplify Console (Recommended)

1. **Go to AWS Amplify Console:**
   - Navigate to: https://console.aws.amazon.com/amplify/
   - Region: `us-east-2` (Ohio)

2. **Create New App:**
   - Click "New app" → "Host web app"
   - Choose "GitHub" as source
   - Authorize AWS Amplify to access your GitHub account

3. **Select Repository:**
   - Repository: `tornari2/RoomDetectionAI`
   - Branch: `main`
   - Click "Next"

4. **Configure Build Settings:**
   - App name: `room-detection-ai-frontend`
   - The build settings will auto-populate from `amplify.yml`
   - Click "Advanced settings"

5. **Add Environment Variables:**
   ```
   Key: VITE_API_BASE_URL
   Value: https://yady49pjx3.execute-api.us-east-2.amazonaws.com/dev
   ```
   
   **IMPORTANT:** Replace `/dev` with your actual stage name if different

6. **Review and Deploy:**
   - Review all settings
   - Click "Save and deploy"
   - Wait for deployment (3-5 minutes)

### Option B: AWS CLI Deployment

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Configure Amplify
amplify configure

# Initialize Amplify in your project
cd /Users/michaeltornaritis/Desktop/WK4_RoomDetectionAI
amplify init

# Add hosting
amplify add hosting
# Choose: Amazon CloudFront and S3

# Deploy
amplify publish
```

## Step 3: Configure CORS on API Gateway

Your API Gateway needs to allow requests from your Amplify domain:

```bash
# Get your Amplify domain after deployment
# It will be something like: https://main.d1234abcd5678.amplifyapp.com

# Update API Gateway CORS settings:
aws apigateway update-rest-api \
  --rest-api-id yady49pjx3 \
  --region us-east-2 \
  --patch-operations \
    op=replace,path=/*/OPTIONS/integration/cacheKeyParameters,value='["method.request.header.Access-Control-Request-Headers","method.request.header.Access-Control-Request-Method","method.request.header.Origin"]'
```

**OR** Update CORS in Lambda handler (already configured in `lambda/handler.py`):
```python
headers = {
    'Access-Control-Allow-Origin': 'https://your-amplify-domain.amplifyapp.com',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST,GET,OPTIONS'
}
```

## Step 4: Test the Deployment

1. **Access Your App:**
   - URL: `https://main.d[your-app-id].amplifyapp.com`
   - Or use custom domain if configured

2. **Test Upload:**
   - Upload a blueprint image
   - Verify processing works
   - Check detected rooms display correctly

## Step 5: Set Up Custom Domain (Optional)

1. In Amplify Console, go to "Domain management"
2. Add your domain (e.g., `roomdetection.yourcompany.com`)
3. Follow DNS configuration instructions
4. Update CORS settings with new domain

## Continuous Deployment

Once connected to GitHub:
- ✅ Automatic deployments on push to `main`
- ✅ Preview deployments for pull requests
- ✅ Build logs available in Amplify Console

## Environment Variables Reference

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_BASE_URL` | `https://yady49pjx3.execute-api.us-east-2.amazonaws.com/dev` | API Gateway endpoint |

## Troubleshooting

### Build Fails
- Check build logs in Amplify Console
- Verify `amplify.yml` configuration
- Ensure all dependencies in `package.json`

### API Calls Fail
- Verify `VITE_API_BASE_URL` is set correctly
- Check CORS configuration
- Ensure Lambda has proper permissions
- Check API Gateway stage deployment

### Blank Page After Deploy
- Check browser console for errors
- Verify build artifacts in `frontend/dist`
- Check routing configuration

## Architecture

```
GitHub Repo (main branch)
    ↓
AWS Amplify
    ↓ (builds frontend)
CloudFront + S3
    ↓ (API calls)
API Gateway
    ↓
Lambda Function
    ↓
SageMaker Endpoint
```

## Cost Estimate

**AWS Amplify:**
- Build minutes: ~5 min/deployment
- Storage: ~50 MB
- Data transfer: Depends on usage
- Estimated: $0.01 per deployment + $0.15/GB transfer

**Total Monthly Cost (low traffic):**
- ~$5-10/month for 100 deploys + 10 GB transfer

## Monitoring

- **Amplify Console**: Build history, logs, metrics
- **CloudWatch**: Lambda logs, API Gateway logs
- **CloudFront**: CDN performance metrics

## Next Steps After Deployment

1. ✅ Test end-to-end workflow
2. ✅ Monitor CloudWatch logs
3. ✅ Set up custom domain
4. ✅ Configure alerts for errors
5. ✅ Add SSL certificate
6. ✅ Set up CI/CD workflows

---

**Your API Endpoint:**
```
https://yady49pjx3.execute-api.us-east-2.amazonaws.com/dev
```

**Deploy Command (Quick Start):**
```bash
# Go to: https://console.aws.amazon.com/amplify/
# Connect GitHub repo: tornari2/RoomDetectionAI
# Add env var: VITE_API_BASE_URL=https://yady49pjx3.execute-api.us-east-2.amazonaws.com/dev
# Click "Save and deploy"
```

Good luck with your deployment! 🚀

