import type { components } from './api.generated'
export type Call = components['schemas']['CallResult']
export type Sample = components['schemas']['SampleInfo']
export type Health = components['schemas']['Health']
export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status}). Please try again.`)
  }
  return response.json()
}
export const active = (call: Call | null) => call?.status === 'queued' || call?.status === 'processing'
