# R3F Architecture

## Suggested boundaries
- `<ExperienceCanvas>`: canvas configuration, DPR, frameloop, camera, error fallback.
- `<Scene>`: scene graph only.
- `<Environment>`: lighting/environment.
- `<Model>` components: asset loading + local animation.
- `<Rig>`: camera and scroll choreography.
- `<Effects>`: post-processing, optional and tiered.
- DOM overlay: semantic content, controls, labels, loading, fallback.

## State
Keep high-frequency render state in refs/MotionValues/external animation values rather than React state. React state is for semantic changes, not 60fps position updates.

## Lifecycle
Cache/reuse loaded assets when safe. Dispose resources that are created manually. Cancel timers/listeners and stop external timelines on unmount.

## Next.js
Keep WebGL canvas in a client boundary. Dynamically import heavy 3D modules when server rendering is irrelevant. Keep SEO/content in server-rendered DOM where possible.
