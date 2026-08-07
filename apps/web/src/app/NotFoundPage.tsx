import { useLanguage } from '../i18n/LanguageProvider';

export function NotFoundPage() {
  const { messages } = useLanguage();

  return (
    <section aria-label="Route not found">
      <h2>{messages.notFoundHeading}</h2>
      <p>{messages.notFoundBody}</p>
    </section>
  );
}
