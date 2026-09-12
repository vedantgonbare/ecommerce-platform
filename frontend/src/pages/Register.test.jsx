import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../test/test-utils'
import Register from './Register'
import { api } from '../api/client'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../api/client', () => ({
  api: {
    post: vi.fn(),
  },
}))

describe('Register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('registers a new user and redirects to login, not to home', async () => {
    api.post.mockResolvedValue({ id: 'user-123', email: 'newuser@example.com' })

    renderWithProviders(<Register />)

    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: 'newuser@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'SecurePass123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        email: 'newuser@example.com',
        password: 'SecurePass123!',
      })
    })

    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })
})