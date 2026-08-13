# Test Matrix

At minimum test:
- Chrome desktop: mouse + trackpad
- Safari desktop
- Firefox desktop
- iOS Safari touch
- Android Chrome touch
- keyboard-only
- reduced motion
- slower network
- CPU throttling / mid-range performance profile
- resize/orientation change
- route back/forward navigation
- tab hidden/visible transition

For 3D also test:
- WebGL failure/fallback path
- low DPR vs high DPR
- offscreen canvas behavior
- context/resource cleanup after navigation
- WebGPU capability failure if an optional WebGPU path exists
