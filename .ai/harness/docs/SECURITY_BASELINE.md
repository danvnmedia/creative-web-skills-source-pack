# Security & Privacy Baseline

## Standards baseline
- OWASP ASVS 5.0 Level 1 for ordinary web applications.
- Elevate controls for sensitive data, authentication, multi-tenancy, financial/education/children data, admin capabilities and high-impact actions.
- Use OWASP Top 10:2025 categories during adversarial review.

A checklist is not proof. Tests and configuration/runtime evidence are required for important claims.

## 1. Access control
- Authorization is enforced server-side for every protected action/object.
- Never trust a client-provided user/tenant/role identifier without authoritative validation.
- Test horizontal and vertical privilege escalation.
- Multi-tenant data queries must carry tenant boundary at the authoritative layer.
- Admin/debug endpoints are protected and auditable.

## 2. Authentication/session
- Use established provider/framework primitives where possible.
- Secure cookie/session/token settings appropriate to the platform.
- Expiry/revocation/logout behavior is intentional.
- Re-authenticate or require stronger confirmation for high-risk actions where appropriate.
- Do not invent custom cryptography/auth protocols without compelling reason.

## 3. Input and injection
- Validate type, length, format and allowed values at trust boundaries.
- Parameterize database queries.
- Contextually encode output.
- Treat URLs, redirects, templates, shell commands, HTML and AI/tool inputs as untrusted.
- Bound request/body/query complexity.

## 4. File/media upload
- Limit size/count/type.
- Validate content/signature as appropriate, not extension only.
- Store with safe generated names and non-executable behavior.
- Scan/quarantine when risk requires it.
- Enforce authorization on read/delete, not only upload.

## 5. Secrets/configuration
- No secrets in source, client bundle, logs, analytics or screenshots.
- Least privilege for service accounts/tokens.
- Separate environments.
- Rotate/revoke compromised credentials.
- Fail closed for security-sensitive config when safe to do so.

## 6. Privacy/data lifecycle
- Collect the minimum needed data.
- Classify sensitive fields.
- Define retention/deletion/export/correction where relevant.
- Avoid raw PII in logs/telemetry.
- Know which external/AI providers receive which data.
- Do not send sensitive data to a model/provider without approved policy and need.

## 7. Abuse and availability security
- Rate limit/cost bound expensive endpoints.
- Protect password/reset/invite/search/upload/AI-generation surfaces from abuse.
- Use quotas and per-user/tenant limits where appropriate.
- Do not allow retries or background jobs to create unbounded work.

## 8. Supply chain
- Lock dependencies.
- Review new dependencies by necessity, maintenance, permissions and known issues.
- Run dependency/security scanning where available.
- Protect build/deploy credentials and artifacts.

## 9. Logging/monitoring
Log meaningful security events without secrets/PII:
- auth failures/anomalies;
- permission denials on sensitive operations;
- admin/high-impact changes;
- rate/abuse events;
- unexpected integrity failures.

## 10. AI-enabled features
When the product uses LLMs/tools:
- treat model output as untrusted;
- separate instructions from untrusted content;
- minimize tool permissions;
- validate tool arguments/actions server-side;
- prevent prompt content from bypassing authorization/business rules;
- bound tokens/cost/rate;
- redact sensitive context;
- do not let model confidence substitute for factual verification.

## High-risk negative test examples
- user A requests user B object ID;
- tenant A changes tenant ID in request;
- non-admin calls admin endpoint;
- expired/invalid session repeats state-changing action;
- upload disguised content/oversized file;
- repeated request/double-click causes duplicate charge/write;
- external callback/webhook replay;
- malformed/huge input stresses parser/query;
- AI prompt attempts to trigger forbidden tool/data action.

## Skill supply-chain gate

Before installing/importing/promoting an Agent Skill, run `.ai/scripts/skill_security_gate.py`. The deterministic gate never executes scanned Skill code and fails closed on resource ceilings. See `docs/harness/SKILL_SECURITY_GATE.md`.
