import { client } from './client'
import type { AssetsListResponse } from '../../types/entities'
import type { AddAssetRequest, AddAssetResponse } from '../../types/api'

export async function fetchAssets(
  includeClosed = false,
): Promise<AssetsListResponse> {
  const { data } = await client.get<AssetsListResponse>('/assets', {
    params: { include_closed: includeClosed },
  })
  return data
}

export async function addAsset(
  payload: AddAssetRequest,
): Promise<AddAssetResponse> {
  const { data } = await client.post<AddAssetResponse>('/assets', payload)
  return data
}
