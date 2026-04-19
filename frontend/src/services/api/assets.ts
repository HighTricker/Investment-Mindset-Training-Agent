import { client } from './client'
import type { AssetsListResponse } from '../../types/entities'
import type {
  AddAssetRequest,
  AddAssetResponse,
  CloseAssetRequest,
} from '../../types/api'

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

export async function closeAsset(
  assetId: number,
  payload: CloseAssetRequest,
): Promise<void> {
  await client.request({
    method: 'DELETE',
    url: `/assets/${assetId}`,
    data: payload,
  })
}
