# Shader Recipe Vocabulary

## Noise dissolve
Sample noise; compare against progress threshold; soften edge with smoothstep. Add colored edge only if concept supports it. Reduced motion: crossfade.

## Displacement transition
Use one texture/noise field to offset UVs of source/target textures as progress changes. Keep displacement low enough to preserve subject legibility.

## Refraction lens
Derive offset from normal/SDF field; sample background texture with controlled chromatic split. Watch texture reads and edge artifacts.

## Grain/dither
Prefer subtle procedural or small tiling noise. Avoid high-frequency animation that creates compression/flicker issues.

## Flow field particles
Encode velocity from curl/noise/field; integrate position; recycle particles. Make density adaptive.

## SDF shape mask
Use signed-distance primitives for crisp procedural geometry and morphing. Combine with smooth min/max carefully.

## Feedback trail
Ping-pong render targets. Fade previous frame and composite new content. Limit resolution and stop when not visible.
