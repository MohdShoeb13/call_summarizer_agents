import { describe,it,expect,vi,afterEach } from 'vitest'
import { request } from './api'
afterEach(()=>vi.unstubAllGlobals())
describe('API errors',()=>{
  it('surfaces actionable backend validation errors',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:422,json:async()=>({detail:'Transcript is empty.'})}));await expect(request('/api/calls')).rejects.toThrow('Transcript is empty.')})
  it('handles non-JSON upstream failures',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:502,json:async()=>{throw Error('HTML')}}));await expect(request('/api/calls')).rejects.toThrow('Request failed (502)')})
})
