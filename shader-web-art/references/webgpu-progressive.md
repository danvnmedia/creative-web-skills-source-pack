# Progressive WebGPU

WebGPU can offer modern rendering/compute capabilities but does not have universal browser availability.

## Gate
1. Check secure context and `navigator.gpu`.
2. Request adapter and device; handle null/rejection.
3. Inspect required features/limits.
4. Use a supported path only after successful initialization.
5. Fall back to WebGL, Canvas, CSS, or static poster.

## Suitable reasons
- large compute-based particle simulations
- storage-buffer workflows
- modern post-processing pipelines
- experiments specifically targeting supported devices

## Unsuitable reason
“WebGPU sounds newer.” Do not increase risk with no measurable benefit.
