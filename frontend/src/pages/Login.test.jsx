import { describe, it } from 'vitest'
import { renderWithProviders } from '../test/test-utils'
import Login from './Login'

describe('Login', () => {
  it('renders without crashing', () => {
    renderWithProviders(<Login />)
  })
})