import { useContext } from 'react'
import {
  AssetsContext,
  type AssetsContextValue,
} from '../stores/AssetsContext'

export function useAssets(): AssetsContextValue {
  const ctx = useContext(AssetsContext)
  if (!ctx) {
    throw new Error('useAssets 必须在 <AssetsProvider> 内使用')
  }
  return ctx
}
