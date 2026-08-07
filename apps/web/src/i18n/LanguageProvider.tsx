import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';

import { englishMessages, spanishMessages, type Messages } from './messages';

type Language = 'en' | 'es';

type LanguageContextValue = {
  language: Language;
  messages: Messages;
  toggleLanguage: () => void;
};

const defaultContextValue: LanguageContextValue = {
  language: 'en',
  messages: englishMessages,
  toggleLanguage: () => {},
};

const LanguageContext = createContext<LanguageContextValue>(defaultContextValue);

export function LanguageProvider({ children }: PropsWithChildren) {
  const [language, setLanguage] = useState<Language>('en');

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const value = useMemo<LanguageContextValue>(() => {
    return {
      language,
      messages: language === 'en' ? englishMessages : spanishMessages,
      toggleLanguage: () => {
        setLanguage((currentLanguage) => (currentLanguage === 'en' ? 'es' : 'en'));
      },
    };
  }, [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  return useContext(LanguageContext);
}
