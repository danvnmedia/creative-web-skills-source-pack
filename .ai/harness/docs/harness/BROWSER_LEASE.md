# Borrowed Browser Lease

A disposable browser launched for verification is isolated harness runtime and needs no lease. A real logged-in user tab/window has broader authority and must be explicitly borrowed.

Create a lease with a narrow tab/window/origin scope, permitted actions, and short TTL. Validate the lease immediately before each borrowed-context action. Neighboring tabs and windows remain out of scope. Human login/captcha takeover does not expand scope. Return the lease with observable evidence; an expired or returned lease cannot be reused.

Set `traits.borrowed_browser_session=true` so `browser-lease` becomes a trait-derived quality gate.
