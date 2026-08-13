# Motion Pattern Cookbook

## Masked editorial reveal
Still frame first. Wrap line/media in overflow-hidden container. Animate child from 105% to 0% with strong ease-out. Reduced motion: opacity only or immediate.

## Image crop expansion
Start with controlled crop/aspect ratio. Expand container using FLIP/layout animation; preserve focal point. Use as scene continuity, not as a generic zoom.

## Pinned feature sequence
Pin one visual context; advance 2–5 meaningful states. Copy changes should be readable before the next threshold. On mobile shorten or convert to swipe/stack.

## Horizontal gallery
Use horizontal movement only if the spatial metaphor supports it. Preserve vertical page control; show progress/affordance; ensure touch and keyboard alternatives.

## Magnetic/attractor button
Keep displacement subtle and only for fine pointer devices. Never move the hit target unpredictably. Focus state remains stable.

## Kinetic headline
Animate by line/word/character only when typography is a principal visual element. Keep semantic text intact. Avoid 100-character stagger that delays content.

## Shared element transition
Prefer Motion layoutId, GSAP Flip, or View Transitions. One object should visibly persist and change role to create continuity.

## Scroll-linked parallax
Use 2–3 depth layers with restrained ranges. Map to transform, avoid layout properties. Disable large movements under reduced motion and simplify on mobile.
