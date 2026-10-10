import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { readMode, saveMode } from './live'

const ModeContext = createContext({ mode: 'demo', setMode: () => {} })

// One Demo / Live switch for the whole app, remembered per browser.
export function ModeProvider({ children }) {
  const [mode, setModeState] = useState(() => readMode(window.localStorage))
  const setMode = useCallback((m) => {
    setModeState(m)
    saveMode(window.localStorage, m)
  }, [])
  const value = useMemo(() => ({ mode, setMode }), [mode, setMode])
  return <ModeContext.Provider value={value}>{children}</ModeContext.Provider>
}

export const useMode = () => useContext(ModeContext)
