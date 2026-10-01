# Modern motion support and fallback

Research snapshot: 2026-09-30. Recheck browser compatibility for a project's actual support matrix.

- CSS scroll-driven timelines tie animation progress to scroll or view progress. [MDN marks `scroll()` limited availability](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-timeline/scroll), so use `@supports (animation-timeline: scroll())` and keep meaningful content visible without it. Avoid making opacity zero by default.
- Same-document [View Transitions are Baseline 2025 on current browsers](https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition), but older clients still need direct state updates. Restore focus and reading position after a view change.
- [`prefers-reduced-motion` is widely available](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion). Design a calmer variant instead of merely shortening every animation to zero.
- [Motion](https://github.com/motiondivision/motion) supports springs and component/layout transitions; [GSAP](https://github.com/greensock/GSAP) is useful for deterministic timelines. Choose one owner per animated property and inspect each library's license before importing it.

For scroll effects, describe a still fallback first. In a browser check both a supporting and an unsupported/reduced-motion path. A CSS feature check passing does not prove smooth frame pacing; measure the heavy route on a representative device.
