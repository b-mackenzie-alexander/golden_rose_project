import { getStaffIdentityReadiness } from './staffAccountClient';

export type StaticOperationalFallbackPolicy = 'allow' | 'deny' | 'loading';

export async function getStaticOperationalFallbackPolicy(): Promise<StaticOperationalFallbackPolicy> {
  const readiness = await getStaffIdentityReadiness();
  if (!readiness.ok) return 'deny';
  return readiness.value.environment === 'production' ? 'deny' : 'allow';
}

export function staticOperationalFallbacksAllowed(policy: StaticOperationalFallbackPolicy) {
  return policy === 'allow';
}

export function staticOperationalFallbackNotice(policy: StaticOperationalFallbackPolicy, language: 'en' | 'es') {
  if (policy !== 'deny') return null;
  return language === 'es'
    ? 'El modo de produccion muestra solo registros guardados y proyecciones autoritativas; los ejemplos estaticos estan desactivados.'
    : 'Production mode shows saved records and authoritative projections only; static examples are disabled.';
}
