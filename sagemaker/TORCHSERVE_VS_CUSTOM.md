# TorchServe vs Custom inference.py - Comparison

## Current Situation

The SageMaker endpoint is using **TorchServe** (PyTorch's default model serving framework), but it's crashing because:
1. TorchServe expects a `.mar` (Model Archive) file format
2. We're providing a `.pt` (PyTorch) file directly
3. TorchServe needs a custom handler to work with YOLOv8

## Option 1: Use TorchServe (What's Currently Happening)

### Pros:
- ✅ Already configured in PyTorch inference container
- ✅ Standard approach for PyTorch models
- ✅ Built-in features (batching, multi-model serving, etc.)

### Cons:
- ❌ Need to convert YOLOv8 `.pt` model to `.mar` format
- ❌ Need to create a TorchServe handler script
- ❌ More complex setup
- ❌ Currently crashing (workers dying)

### What's Needed:
1. Create a TorchServe handler for YOLOv8
2. Use `torch-model-archiver` to create `.mar` file
3. Package model as `.mar` instead of `.pt`
4. Configure TorchServe handler

### Estimated Effort: 2-3 hours

---

## Option 2: Use Custom inference.py (What We're Trying)

### Pros:
- ✅ Already written and tested
- ✅ Direct control over inference logic
- ✅ Works directly with YOLOv8 `.pt` files (no conversion)
- ✅ Simpler for our use case
- ✅ Matches our API spec exactly

### Cons:
- ❌ Need correct container base (training container works)
- ❌ Slightly larger image size

### What's Needed:
1. ✅ Use PyTorch training container (supports custom scripts)
2. ✅ Set `SAGEMAKER_PROGRAM=inference.py` (already done)
3. ✅ Rebuild Docker image (in progress)

### Estimated Effort: 30 minutes (waiting for build)

---

## Recommendation

**Stick with custom inference.py** because:
1. ✅ Code is already written and working
2. ✅ Simpler - no model conversion needed
3. ✅ More control over response format
4. ✅ Faster to fix (just need correct container)

**However**, if you want to use TorchServe:
- We'd need to create a handler and convert the model
- Might be more "standard" but adds complexity
- Could be more maintainable long-term

---

## Current Status

- **Custom inference.py approach**: Build in progress (using training container)
- **TorchServe approach**: Would require new work (handler + model conversion)

Which approach would you prefer?

