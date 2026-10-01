# Component verification checklist

Use only rows that apply to the component. Record observed results rather than checking boxes from source review alone.

| Area | Observable check |
|---|---|
| Semantics | Control has the right element, accessible name, and state; decorative layers are hidden from assistive technology. |
| Keyboard | Tab order is logical; Enter/Space activates actions; Escape closes a dismissible layer; focus returns to its trigger. |
| Pointer/touch | Primary action works without hover; target is usable at a 390px viewport; drag has a non-drag alternative. |
| Visual | Text and control contrast remain readable in each supported theme; focus is visible on every interactive state. |
| Motion | Reduced-motion mode removes large travel/continuous motion while keeping state changes understandable. |
| Responsive | Labels do not clip, overlap, or force accidental horizontal scrolling at narrow widths. |
| Failure | Content and navigation stay available if animation, media, or optional browser APIs fail. |

For dialog, menu, or tabs, also inspect inactive content and current/selected state announcements. For a carousel, provide controls with names and a static reading order.
