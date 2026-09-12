import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../test/test-utils'
import Login from './Login'
import { api } from '../api/client'

vi.mock('../api/client', () => ({
  api: {
    post: vi.fn(),
  },
}))

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    renderWithProviders(<Login />)
  })

  it('submits email and password to the login endpoint', async () => {
    api.post.mockResolvedValue({ message: 'Login successful' })

    renderWithProviders(<Login />)

    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'SecurePass123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'SecurePass123!',
      })
    })
  })
})