import { client } from './client'
import type { AssetsListResponse } from '../../types/entities'

export async function fetchAssets(
  includeClosed = false,
): Promise<AssetsListResponse> {
  const { data } = await client.get<AssetsListResponse>('/assets', {
    params: { include_closed: includeClosed },
  })
  return data
}
