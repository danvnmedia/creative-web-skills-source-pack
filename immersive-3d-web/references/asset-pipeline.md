# 3D Asset Pipeline

## Geometry
Preserve silhouette and deformation-critical topology. Remove hidden internals unless needed. Use instancing for repeated meshes.

## Textures
Size to actual projected use. Avoid 4K textures on tiny objects. Compress and share maps when possible. Watch alpha-heavy textures and overdraw.

## glTF/GLB
Prefer GLB for delivery simplicity. Preserve useful node names. Strip unused animations/materials. Consider Meshopt/Draco based on decode/runtime tradeoffs.

## Animation
Bake artist-authored skeletal/morph animation into clips. Use procedural or timeline tools for camera and simple transforms. Avoid duplicating the same animation system at multiple layers.

## Loading
Show a meaningful poster/first frame. Preload only assets required for the first visible scene. Lazy-load deeper chapters.
