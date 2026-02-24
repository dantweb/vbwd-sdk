Here is a complete **Markdown document** you can copy-paste into a file (e.g. `tech-spec-skin-analysis-microservice.md`). It consolidates the discussed flow, requirements, models, architecture, and cost estimates into a formal technical task/specification for the Python microservice.

```markdown
# Technical Specification: Skin Analysis Microservice (Python)

**Version**: 1.0  
**Date**: February 2026  
**Purpose**: Tiny, stateless Python microservice for batch / on-demand inference:  
- Filter incoming images (quality + NSFW / pornography rejection)  
- Perform medical-grade skin lesion analysis (if passed)  

**Scope**: Only the inference core — no frontend, no persistent storage, no user auth, no orchestration layer. Input = image bytes or URL, output = JSON.

## 1. Functional Requirements

### 1.1 Endpoints

- **POST /analyze** (main endpoint — single image)  
  - Input: multipart/form-data with file (`image`) or JSON with `image_url`  
  - Output: JSON (see §4)  

- **POST /batch-analyze** (optional, for efficiency)  
  - Input: list of images / URLs  
  - Output: list of results  

### 1.2 Processing Pipeline (Mandatory Steps – Sequential)

1. **Image Preprocessing**  
   - Load & validate format (JPEG, PNG, WEBP; reject others)  
   - Resize to max 1024×1024 (preserve aspect)  
   - Normalize (mean/std from model training)

2. **NN1 – Validation & Safety Filter** (must reject ~20–40% real-world uploads)  
   - **Quality checks**  
     - Blur/sharpness: MUSIQ or MANIQA (no-reference IQA) or BRISQUE + Laplacian variance fallback  
     - Reject if quality score too low  
   - **NSFW / Pornography detection**  
     - Primary: NudeNet (still widely used & fast in 2026) or modern CLIP-based / ViT-based NSFW detector (e.g. LAION Safety Checker or nsfw_image_detection from HF)  
     - Reject if nudity / explicit / porn probability > 0.60–0.75 (tunable)  
   - **Skin plausibility check** (soft)  
     - Optional simple skin segmentation (U-Net lite or threshold-based HSV) → reject if <15–20% skin pixels  

   → If **any rejection criterion** met → early return with rejection reason

3. **NN2 – Dermatology Analysis** (only if NN1 passes)  
   - Detect & classify skin lesions / conditions  
   - Supported output classes (minimum):  
     - pigmented lesions: melanoma, atypical nevus, seborrheic keratosis, BCC, AKIEC, etc.  
     - other: rash/inflammation, burn (1st/2nd/3rd degree), vascular, etc.  
   - Optional: lesion segmentation → crop → classify (improves accuracy ~5–10%)  
   - Output includes probabilities, description, urgency recommendation & strong medical disclaimer

## 2. Recommended Models (2026 realistic open-source choices)

| Stage | Model Family                  | Recommended Concrete Model                  | Source / HF Repo                          | Approx. Params | Expected Latency (T4/L4 GPU, batch=1) | Notes |
|-------|-------------------------------|---------------------------------------------|-------------------------------------------|----------------|----------------------------------------|-------|
| NN1   | NSFW classifier               | NudeNet v2 or LAION/CLIP-based NSFW         | notAI-tech/NudeNet or HF nsfw detectors   | ~10–80 M       | 10–50 ms                               | Very fast; can run on CPU if needed |
| NN1   | Quality (NR-IQA)              | MUSIQ or HyperIQA                           | google-research/hyperiqa or similar       | ~30–60 M       | 20–80 ms                               | No-reference = ideal |
| NN2   | Skin lesion classification    | ConvNeXt-T / EfficientNetV2 / Swin-Tiny fine-tuned on ISIC 2024 + HAM10000 + PAD-UFES | timm lib or HF (search "dermatology", "isic") | 30–100 M       | 40–150 ms                              | Multi-label or hierarchical head |
| NN2   | Optional segmentation         | MobileSAM / EfficientSAM-lite or U-Net++    | HF or segment-anything                    | ~20–50 M       | +50–120 ms                             | Improves focus on lesion |

- Use **timm** library for easy model loading & inference  
- Quantize to fp16 / int8 (Torch or ONNX) → 1.5–3× speedup & lower VRAM  
- Prefer models with Apache 2.0 / MIT license

## 3. Technical Stack & Dependencies

- **Language**: Python 3.10–3.12  
- **Framework**: FastAPI (async)  
- **Inference**: PyTorch 2.2+ (with `torch.compile` if possible) or ONNX Runtime  
- **Core libs**:
  - `fastapi`, `uvicorn`, `pydantic`
  - `torch`, `torchvision`, `timm`
  - `pillow`, `numpy`, `opencv-python-headless`
  - `nudenet` (or huggingface-hub for NSFW models)
  - `requests` (for URL downloads)
- **Optional**: `prometheus_client` for metrics, `structlog` for logging

**Deployment targets** (serverless GPU preferred):

- RunPod Serverless, Modal.com, Banana.dev, Baseten, HF Inference Endpoints  
- GPU: L4 / A10 / RTX 4090 equiv. sufficient (24 GB VRAM nice-to-have)  
- Cold start target: < 4–10 s (Modal / RunPod Active workers help)

## 4. Output JSON Schema

```json
{
  "status": "success" | "rejected_quality" | "rejected_nsfw" | "rejected_not_skin" | "error",
  "reason": "optional string if rejected",
  "lesion_detected": boolean | null,
  "main_description": "human-readable summary or null",
  "predictions": [
    {
      "label": "seborrheic keratosis",
      "probability": 0.58,
      "risk_level": "low" | "moderate" | "high" | null
    },
    ...
  ],
  "urgency": "consult within days / weeks / no urgency" | null,
  "disclaimer": "This is NOT a medical diagnosis. See a qualified dermatologist. AI output only.",
  "inference_time_ms": 320,
  "model_versions": {
    "nn1_quality": "musiq-2023",
    "nn1_nsfw": "nudenet-v2",
    "nn2": "convnext-t-isic-2025"
  }
}
```

## 5. Performance & Cost Targets

**Batch example (one-time / monthly)**:

- 20 000 images → NN1 only  
- 10 000 images → full pipeline (NN1 + NN2)

**Estimated cost (serverless GPU, Feb 2026 pricing)**:

| Provider       | GPU type       | ~$/GPU-hour | Total for 30k images (optimistic) | Total realistic range |
|----------------|----------------|-------------|-----------------------------------|-----------------------|
| RunPod / Modal | L4 / A10 equiv | $0.4–1.0    | $3–12                             | **$8–25**             |
| High-end       | A100 slice     | $1.5–3.0    | $10–35                            | $15–50                |

→ **Sweet spot expectation**: $10–25 for 30 000 images (very affordable)  
→ Tips: aggressive batching (16–64), quantization, single pipeline pass (NN1 → NN2 without reload)

## 6. Non-Functional Requirements

- **Security**: No persistent storage of images; process in memory; delete after inference  
- **Logging**: Structured logs (request ID, status, timings, rejection reason)  
- **Error handling**: Graceful failures (invalid image, timeout, OOM) → HTTP 4xx/5xx + JSON  
- **Rate limiting**: Optional (e.g. slowapi)  
- **Monitoring**: Prometheus metrics (requests, latency, rejection rate, GPU util)  
- **Compliance note**: Output **must** include strong disclaimer; service not intended as standalone diagnostic tool

## 7. Acceptance Criteria

- NN1 rejects >90% obvious porn/blurry images in test set  
- NN2 achieves ≥85–92% top-3 accuracy on ISIC-like hold-out set  
- Single image latency < 1.5 s (p95) on L4 GPU  
- Cost per 1 000 full analyses < $1.0 (optimistic)  
- 100% uptime on cold-start serverless (no unhandled exceptions)

## Next Steps

1. Select & download/fine-tune concrete models  
2. Implement pipeline in FastAPI  
3. Benchmark latency & cost on target platform  
4. Write unit/integration tests (synthetic & real images)

---
**End of Specification**
```

Feel free to adjust thresholds, add more endpoints, or change model preferences. If you want sections expanded (e.g. detailed code structure, Dockerfile, or CI/CD notes), let me know.