import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

function OrderDetail() {
  const { id } = useParams()
  const queryClient = useQueryClient()

  const { data: order, isLoading, error } = useQuery({
    queryKey: ['order', id],
    queryFn: () => api.get(`/orders/${id}`),
  })

  const cancelOrder = useMutation({
    mutationFn: () => api.patch(`/orders/${id}/cancel`),
    onSuccess: (data) => {
      queryClient.setQueryData(['order', id], data)
    },
  })
  if (isLoading) return <p className="p-8">Loading order...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load order: {error.message}</p>

  const canCancel = order.status === 'pending'
  return (
    <div className="p-8 max-w-2xl mx-auto">
      <Link to="/orders" className="text-ink underline text-sm">← Back to orders</Link>

      <h1 className="font-display text-2xl text-ink mt-2">Order #{order.id.slice(0, 8)}</h1>
      <p className="text-ink-muted mt-1 capitalize">Status: {order.status}</p>
      <p className="text-ink-muted">Total: ${order.total}</p>
      <p className="text-sm text-ink-muted">
        Placed on {new Date(order.created_at).toLocaleDateString()}
      </p>

      <div className="flex flex-col gap-3 mt-6">
        {order.items.map((item) => (
          <div key={item.product_id} className="border-b border-line pb-2">
            <p className="font-medium text-ink">{item.product_name}</p>
            <p className="text-sm text-ink-muted">
              Qty {item.quantity} × ${item.unit_price}
            </p>
          </div>
        ))}
      </div>

      {canCancel && (
        <div className="mt-6">
          <button
            onClick={() => cancelOrder.mutate()}
            disabled={cancelOrder.isPending}
            className="bg-red-600 text-white px-4 py-2 rounded-xs disabled:opacity-50"
          >
            {cancelOrder.isPending ? 'Cancelling...' : 'Cancel Order'}
          </button>
          {cancelOrder.error && (
            <p className="text-red-600 text-sm mt-2">{cancelOrder.error.message}</p>
          )}
        </div>
      )}
    </div>
  )
}

export default OrderDetail