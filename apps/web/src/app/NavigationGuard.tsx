import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useBlocker } from 'react-router';
import { NavigationGuardContext } from './navigationGuardContext';

/** Keep in-memory drafts and immutable retry commands mounted across history traversal. */
export function NavigationGuard({ children }: { children: ReactNode }) {
  const [blocked, setBlocked] = useState(false);
  const blocker = useBlocker(blocked);
  useEffect(() => {
    if (blocker.state === 'blocked') blocker.reset();
  }, [blocker]);
  return <NavigationGuardContext value={setBlocked}>{children}</NavigationGuardContext>;
}
