# UX/UI Baseline

## Principle
A UI is not “done” when the screenshot looks attractive. It is done when target users can complete the job quickly, understand system state, recover from failure, and use it on real devices/input methods.

## Required design states
For every meaningful interactive flow consider:
- first use/onboarding;
- loading/skeleton/progress;
- empty;
- partial data;
- validation error;
- server/network error;
- permission denied/auth expired;
- success;
- undo/retry where useful;
- offline/degraded state where applicable.

## Interaction quality
- One clear primary action per decision area.
- Prevent accidental double-submit and duplicate side effects.
- Preserve user input after recoverable errors.
- Disable or explain unavailable actions.
- Do not use color alone to communicate state.
- Focus must move predictably after dialogs/errors/navigation.
- Destructive actions require appropriate confirmation or undo.
- Respect reduced motion.

## Responsive quality
Verify at least:
- narrow mobile around 320–390 CSS px;
- common tablet breakpoint if product supports tablets;
- normal desktop;
- long content, zoomed text and localization.

Avoid:
- horizontal overflow for primary content;
- controls hidden behind mobile keyboard;
- fixed-height panels that clip content;
- hover-only critical actions.

## Accessibility
Default target: WCAG 2.2 AA when applicable.

Minimum habits:
- semantic elements before ARIA;
- logical headings/landmarks;
- labels/names for controls;
- keyboard operation;
- visible, unobscured focus;
- sufficient contrast;
- accessible authentication/forms;
- target sizes that meet applicable criteria; prefer ~44 CSS px touch targets on mobile for comfort;
- screen-reader-friendly dynamic feedback.

## Perceived performance
- show immediate acknowledgement after input;
- reserve layout space to reduce shifts;
- use optimistic UI only when rollback/failure is safe and truthful;
- progressive/lazy loading must not trap the user;
- avoid unnecessary animation before task completion.

## Visual QA
Use screenshots/real browser inspection where available for:
- alignment and spacing consistency;
- clipping/overflow;
- focus/hover/disabled/error states;
- light/dark themes if supported;
- image aspect/cropping;
- layout shift after data loads.
