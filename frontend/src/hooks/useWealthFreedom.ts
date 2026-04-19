import { useContext } from 'react'
import {
  WealthFreedomContext,
  type WealthFreedomContextValue,
} from '../stores/WealthFreedomContext'

export function useWealthFreedom(): WealthFreedomContextValue {
  const ctx = useContext(WealthFreedomContext)
  if (!ctx) {
    throw new Error('useWealthFreedom 必须在 <WealthFreedomProvider> 内使用')
  }
  return ctx
}
