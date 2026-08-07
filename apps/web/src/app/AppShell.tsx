import { NavLink, Outlet } from 'react-router';

import { useLanguage } from '../i18n/LanguageProvider';

export function AppShell() {
  const { messages, toggleLanguage } = useLanguage();

  return (
    <>
      <header role="banner">
        <h1>{messages.shellHeading}</h1>
        <button className="focus-ring" type="button" onClick={toggleLanguage}>
          {messages.switchLanguage}
        </button>
      </header>
      <nav aria-label={messages.primaryNavigation}>
        <ul>
          <li>
            <NavLink className="focus-ring" to="/employers">
              {messages.employersNav}
            </NavLink>
          </li>
        </ul>
      </nav>
      <main role="main">
        <Outlet />
      </main>
    </>
  );
}
