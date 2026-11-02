import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import ProductImage from './ProductImage'

afterEach(cleanup)

describe('ProductImage', () => {
  it('renders the image when a src is given', () => {
    render(<ProductImage src="/products/a.jpg" alt="Yoga Mat" />)
    expect(screen.getByRole('img', { name: 'Yoga Mat' })).toBeTruthy()
  })

  it('shows no image when src is missing', () => {
    render(<ProductImage src={null} alt="Yoga Mat" />)
    expect(screen.queryByRole('img')).toBeNull()
  })

  it('removes the image when it fails to load', () => {
    render(<ProductImage src="https://example.invalid/nope.jpg" alt="Yoga Mat" />)
    fireEvent.error(screen.getByRole('img', { name: 'Yoga Mat' }))
    expect(screen.queryByRole('img')).toBeNull()
  })
})