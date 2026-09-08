import { render,screen,fireEvent } from '@testing-library/react'
import { describe,it,expect,vi } from 'vitest'
import { Button } from './button'
describe('Button',()=>{
  it('does not submit duplicate actions when disabled',()=>{const click=vi.fn();render(<Button disabled onClick={click}>Analyzing</Button>);fireEvent.click(screen.getByRole('button'));expect(click).not.toHaveBeenCalled()})
  it('preserves native link semantics for navigation',()=>{render(<Button asChild><a href="/workspace">Analyze</a></Button>);expect(screen.getByRole('link',{name:'Analyze'})).toHaveAttribute('href','/workspace')})
})
