#!/usr/bin/env python3
import re, sys
sys.dont_write_bytecode=True
from _common import root_from_script, load_json

def errors_for(p:dict)->list[str]:
    errors=[]; version=int(p.get('version') or 1)
    if version not in {1,2,3}: errors.append('provider policy version must be 1, 2, or 3')
    if p.get('strategy')!='gemini-free-first': errors.append('strategy should remain explicit; expected gemini-free-first for this harness profile')
    g=p.get('gemini',{})
    if g.get('quota_scope')!='project': errors.append('Gemini quota_scope must be project; Google rate limits are not per API key')
    if g.get('official_sdk_js')!='@google/genai': errors.append('official JS SDK must be @google/genai')
    privacy=p.get('privacy',{})
    if privacy.get('client_side_provider_keys_forbidden') is not True: errors.append('client-side provider keys must be forbidden')
    if privacy.get('allow_free_tier_for_sensitive_data') is not False: errors.append('free-tier sensitive-data default must be false')
    safety=p.get('safety',{})
    if safety.get('paid_fallback_requires_explicit_project_policy') is not True: errors.append('paid fallback must require explicit project policy/budget')
    if version==1:
        if safety.get('never_use_rotation_to_evade_provider_quotas_or_terms') is not True: errors.append('legacy v1 quota/terms anti-evasion guard must be enabled')
        return errors
    af=(p.get('routing') or {}).get('authorized_capacity_failover') or {}
    required_true=('enabled','independent_quota_scope_only','free_to_free','free_to_paid_requires_budget_authorization','paid_to_eligible_alternative','same_scope_credentials_are_not_new_capacity','different_eligible_capacity_may_run_during_other_scope_cooldown')
    for key in required_true:
        if af.get(key) is not True: errors.append('authorized_capacity_failover.'+key+' must be true')
    if safety.get('never_bypass_provider_restrictions_or_unapproved_spend_caps') is not True: errors.append('provider restrictions and unapproved spend caps must remain fail-closed')
    if safety.get('authorized_failover_is_not_treated_as_quota_evasion') is not True: errors.append('v2+ must distinguish authorized failover from quota evasion')
    if 'never_use_rotation_to_evade_provider_quotas_or_terms' in safety: errors.append('deprecated ambiguous rotation flag must not appear in v2+')
    bounds=(p.get('routing') or {}).get('deadline_and_budget_bounds') or {}
    for key in ('bounded_provider_hops','bounded_total_attempts','paid_spend_must_be_pre_authorized'):
        if bounds.get(key) is not True: errors.append('deadline_and_budget_bounds.'+key+' must be true')
    if version==2:
        return errors
    routing=p.get('routing') or {}
    gate=routing.get('billing_target_budget_gate') or {}
    required_gate=(
      'enabled','evaluate_actual_billing_target_before_execution','paid_fallback_rechecks_all_applicable_configured_budgets',
      'zero_cost_primary_never_exempts_paid_target','budget_verdict_is_read_only_before_reservation','reserve_only_after_target_selected',
      'reservation_must_be_atomic','release_reservation_when_target_not_executed','unknown_paid_target_cost_or_budget_scope_fails_closed',
      'budget_denial_skips_target_without_blocking_eligible_free_target')
    for key in required_gate:
        if gate.get(key) is not True: errors.append('billing_target_budget_gate.'+key+' must be true')
    graph=routing.get('fallback_graph_validation') or {}
    for key in ('validate_before_runtime','reject_malformed_graph','require_target_capability_metadata','require_paid_target_budget_metadata'):
        if graph.get(key) is not True: errors.append('fallback_graph_validation.'+key+' must be true')
    cb=routing.get('circuit_breaker') or {}
    for key in ('half_open_probe','failure_accounted_to_actual_target_scope'):
        if cb.get(key) is not True: errors.append('circuit_breaker.'+key+' must be true in v3')
    return errors

def main():
    root=root_from_script(); p=load_json(root/'.ai/AI_PROVIDER_POLICY.json'); errors=errors_for(p)
    raw=(root/'.ai/AI_PROVIDER_POLICY.json').read_text(encoding='utf-8')
    if re.search(r'AIza[0-9A-Za-z_-]{20,}|\bsk-[A-Za-z0-9_-]{12,}',raw): errors.append('hard-coded secret-looking value in provider policy')
    if errors:
        print('PROVIDER POLICY: FAIL'); [print(f'- {e}') for e in errors]; raise SystemExit(1)
    print('PROVIDER POLICY: PASS')
if __name__=='__main__': main()
