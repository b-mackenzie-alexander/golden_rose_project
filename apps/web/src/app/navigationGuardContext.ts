import { createContext } from 'react';
export const NavigationGuardContext = createContext<((blocked: boolean) => void) | null>(null);
