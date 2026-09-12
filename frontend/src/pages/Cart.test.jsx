import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../test/test-utils'
import Cart from './Cart'
import { api } from '../api/client'

vi.mock('../api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('Cart checkout', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    delete window.location
    window.location = { href: '' }
  })

  it('creates an order, requests a checkout session, and redirects to it', async () => {
    api.get.mockResolvedValue({
      items: [
        {
          id: 'item-1',
          product_id: 'prod-1',
          product_name: 'Test Product',
          product_price: '25.00',
          quantity: 2,
        },
      ],
      subtotal: '50.00',
    })

    api.post
      .mockResolvedValueOnce({ id: 'order-123' })
      .mockResolvedValueOnce({ checkout_url: 'https://checkout.stripe.com/session-abc' })

    renderWithProviders(<Cart />)

    const checkoutButton = await screen.findByRole('button', { name: /proceed to checkout/i })
    checkoutButton.click()

    await waitFor(() => {
      expect(window.location.href).toBe('https://checkout.stripe.com/session-abc')
    })

    expect(api.post).toHaveBeenNthCalledWith(1, '/orders/')
    expect(api.post).toHaveBeenNthCalledWith(2, '/orders/order-123/checkout')
  })
})