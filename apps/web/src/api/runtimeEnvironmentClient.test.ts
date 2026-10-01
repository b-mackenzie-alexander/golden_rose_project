import { beforeEach, describe, expect, it, vi } from 'vitest';

import { getStaffIdentityReadiness, type StaffIdentityReadiness } from './staffAccountClient';
import { getStaticOperationalFallbackPolicy, staticOperationalFallbackNotice, staticOperationalFallbacksAllowed } from './runtimeEnvironmentClient';

vi.mock('./staffAccountClient', () => ({
  getStaffIdentityReadiness: vi.fn(),
}));

const readiness: StaffIdentityReadiness = {
  environment: 'develop',
  authMode: 'synthetic',
  staffIdentityBoundary: 'synthetic_private_develop',
  productionStaffAuthReady: false,
  syntheticStaffRuntimeAllowed: true,
  recoveryAndSessionRevocationEvidenceOnly: true,
  requiredOperatorActions: ['replace_synthetic_staff_auth_before_production'],
};

describe('runtimeEnvironmentClient', () => {
  beforeEach(() => {
    vi.mocked(getStaffIdentityReadiness).mockResolvedValue({ ok: true, value: readiness });
  });

  it('allows static operational fallbacks outside production mode', async () => {
    await expect(getStaticOperationalFallbackPolicy()).resolves.toBe('allow');
    expect(staticOperationalFallbacksAllowed('allow')).toBe(true);
    expect(staticOperationalFallbackNotice('allow', 'en')).toBeNull();
  });

  it('denies static operational fallbacks in production mode', async () => {
    vi.mocked(getStaffIdentityReadiness).mockResolvedValue({
      ok: true,
      value: {
        ...readiness,
        environment: 'production',
        authMode: 'staff_oidc',
        staffIdentityBoundary: 'production_oidc_configured',
        productionStaffAuthReady: true,
        syntheticStaffRuntimeAllowed: false,
        requiredOperatorActions: ['confirm_mfa_claim_mapping'],
      },
    });

    await expect(getStaticOperationalFallbackPolicy()).resolves.toBe('deny');
    expect(staticOperationalFallbacksAllowed('deny')).toBe(false);
    expect(staticOperationalFallbackNotice('deny', 'es')).toContain('ejemplos estaticos');
  });

  it('fails closed when readiness cannot be read', async () => {
    vi.mocked(getStaffIdentityReadiness).mockResolvedValue({ ok: false, failure: { kind: 'unavailable' } });

    await expect(getStaticOperationalFallbackPolicy()).resolves.toBe('deny');
  });
});
