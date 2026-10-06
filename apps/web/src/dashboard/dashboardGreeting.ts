export type DashboardLanguage = 'en' | 'es';

function greetingPeriod(now: Date, language: DashboardLanguage) {
  const hour = now.getHours();
  if (hour < 12) return language === 'es' ? 'Buenos días' : 'Good morning';
  if (hour < 17) return language === 'es' ? 'Buenas tardes' : 'Good afternoon';
  return language === 'es' ? 'Buenas noches' : 'Good evening';
}

export function dashboardGreeting(displayName: string | null, language: DashboardLanguage, now = new Date()) {
  const period = greetingPeriod(now, language);
  const name = displayName?.trim();
  return name ? `${period}, ${name}` : period;
}
