# DOM-WebGL Synchronization

## Coordinate bridge
For each enhanced DOM element, derive viewport-relative bounds and map center/size into the canvas coordinate system. Account for device pixel ratio separately from CSS pixels.

## Scheduling
Batch reads before writes. Update geometry on resize/layout change; update position on scroll using a shared scroll state. Avoid separate scroll listeners per item.

## Crop matching
Replicate `object-fit: cover` by comparing source and destination aspect ratios and adjusting UV scale/offset. Test portrait, landscape, and extreme ratios.

## Interaction
Keep the DOM element as the hit target where possible; pass pointer state into shader uniforms. This preserves accessibility and semantics.

## Failure mode
If WebGL fails, the DOM image/video stays visible and usable. Progressive enhancement is the default.
