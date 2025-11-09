# CPU vs GPU for SageMaker Inference

## ⚠️ Important: SageMaker Serverless Inference is CPU-ONLY

**SageMaker Serverless Inference does NOT support GPU instances.** It's CPU-only by design.

## Why CPU Inference Container is Better for Serverless

### Using GPU Training Container (what we tried):
- ❌ GPU libraries add ~5GB+ to image size
- ❌ GPU won't be used (Serverless = CPU only)
- ❌ Larger image = slower cold starts
- ❌ Hit 10GB size limit (18GB > 10GB limit)

### Using CPU Inference Container (current):
- ✅ Optimized for CPU inference
- ✅ Smaller image (~3GB base vs ~8GB)
- ✅ Faster cold starts
- ✅ Same performance (both CPU-only anyway)
- ✅ Fits under 10GB limit

## Performance Comparison

### Serverless Inference (CPU-only)
- **Inference time:** ~1-3 seconds per image
- **Cost:** Pay per request (~$0.00004 per GB-second)
- **Auto-scales:** To zero when idle
- **Best for:** Low/medium traffic, cost-effective

### Real-Time Endpoint (GPU-capable)
- **Inference time:** ~200-500ms per image (with GPU)
- **Cost:** Pay per hour (~$0.50-2.00/hour even when idle)
- **Always running:** No cold starts
- **Best for:** High traffic, low latency needs

## Recommendation

**For your room detection API:**
- ✅ **Serverless + CPU container** is fine for most use cases
- ✅ CPU inference is fast enough (~1-3 seconds)
- ✅ Much more cost-effective
- ✅ Auto-scales to zero when not in use

**Switch to Real-Time + GPU if:**
- You need <500ms inference time
- You have high constant traffic
- Cost is not a concern

## Current Setup

We're using:
- **Serverless Inference** (CPU-only)
- **CPU inference container** (optimized for CPU)
- **Expected performance:** ~1-3 seconds per image

This is the right choice for Serverless Inference!

