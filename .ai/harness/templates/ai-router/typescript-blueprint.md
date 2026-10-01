# TypeScript Provider Router Blueprint

Use this as an architecture sketch, not copy-paste production code.

```ts
type Capability = 'text' | 'code' | 'reasoning' | 'image' | 'audio' | 'video' | 'tools' | 'json';
type Health = 'healthy' | 'cooldown' | 'exhausted' | 'quarantined';

interface QuotaGroup {
  id: string;              // Gemini project / provider quota scope, never raw key
  provider: string;
  health: Health;
  capabilities: Set<Capability>;
  inflight: number;
  availableAfter?: number;
  latencyEwmaMs?: number;
  successRate?: number;
}

interface ProviderAdapter {
  supports(required: Set<Capability>): boolean;
  invoke(req: AIRequest, credentialRef: string): Promise<AIResponse>;
  classify(error: unknown): ProviderFailure;
}
```

Router flow:
1. filter privacy + capability;
2. score healthy quota groups;
3. choose credential within the quota group;
4. invoke with one bounded retry owner;
5. update health/latency/quota state;
6. fallback only on compatible failures/capabilities;
7. keep tool side effects idempotent and outside unsafe whole-turn retries.

For Gemini JS/TS use the current `@google/genai` SDK and its request `httpOptions.retryOptions` where appropriate. Avoid stacking another uncontrolled retry loop around it.
