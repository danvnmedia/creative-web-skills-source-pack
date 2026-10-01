# Worked examples

## Editorial gallery filter

**Request:** Turn image categories into a compact mobile filter with a soft transition.

**Contract:** A labeled group of buttons with one selected category. The selected item exposes `aria-pressed`; all items remain keyboard reachable. Result cards stay in DOM reading order.

**Motion:** A short transform/opacity transition on the indicator. If same-document View Transitions are supported and motion is allowed, they may animate the image group; direct DOM update is the fallback.

**Check:** Tab through every filter, activate with Space, verify selected state and visible focus at 390px, then repeat with reduced motion.

## Product viewer controls

**Request:** Add rotate and explode controls to a 3D object.

**Contract:** Named buttons for rotate/reset/explode with `aria-pressed` where stateful. Dragging is optional; buttons provide the same core information. A static poster and text labels remain usable when WebGL fails.

**Motion:** Spring-like easing may settle the object after direct input. Avoid updating React state on every frame. Reduced motion uses immediate or short changes.

**Check:** Use keyboard only, then touch viewport, then block WebGL/CDN and confirm labels and controls retain a coherent fallback.
