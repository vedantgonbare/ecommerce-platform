import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

function Cart() {
  const queryClient = useQueryClient()

  const { data: cart, isLoading, error } = useQuery({
    queryKey: ['cart'],
    queryFn: () => api.get('/cart/'),
  })

  const updateQuantity = useMutation({
    mutationFn: ({ productId, quantity }) =>
      api.put(`/cart/items/${productId}`, { quantity }),
    onSuccess: (data) => {
      queryClient.setQueryData(['cart'], data)
    },
  })

  const removeItem = useMutation({
    mutationFn: (productId) => api.delete(`/cart/items/${productId}`),
    onSuccess: (data) => {
      queryClient.setQueryData(['cart'], data)
    },
  })

  const checkout = useMutation({
    mutationFn: async () => {
      const order = await api.post('/orders/')
      const session = await api.post(`/orders/${order.id}/checkout`)
      return session
    },
    onSuccess: (session) => {
      window.location.href = session.checkout_url
    },
  })

  if (isLoading) return <p className="p-8">Loading cart...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load cart: {error.message}</p>

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="font-display text-2xl text-ink mb-4">Your Cart</h1>

      {cart.items.length === 0 ? (
        <p className="text-ink-muted">Your cart is empty.</p>
      ) : (
        <>
          <div className="flex flex-col gap-4">
            {cart.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between border-b border-line pb-3">
                <div>
                  <p className="font-medium text-ink">{item.product_name}</p>
                  <p className="text-sm text-ink-muted">${item.product_price} each</p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={(e) =>
                      updateQuantity.mutate({
                        productId: item.product_id,
                        quantity: Number(e.target.value),
                      })
                    }
                    className="border border-line rounded-xs w-16 p-1 text-center text-ink"
                  />
                  <button
                    onClick={() => removeItem.mutate(item.product_id)}
                    className="text-red-600 underline text-sm"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center mt-6">
            <p className="text-lg font-semibold text-ink">Subtotal: ${cart.subtotal}</p>
            <button
              onClick={() => checkout.mutate()}
              disabled={checkout.isPending}
              className="bg-tan text-ink px-4 py-2 rounded-xs font-semibold disabled:opacity-50"
            >
              {checkout.isPending ? 'Redirecting...' : 'Proceed to Checkout'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default Cart