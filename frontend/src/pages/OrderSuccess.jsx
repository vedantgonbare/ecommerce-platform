import { useSearchParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

function OrderSuccess() {
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id')

  const { data: order, isLoading, error } = useQuery({
    queryKey: ['order-success', sessionId],
    queryFn: () => api.get(`/orders/success?session_id=${sessionId}`),
    enabled: !!sessionId,
  })

  if (!sessionId) return <p className="p-8 text-red-600">Missing session ID.</p>
  if (isLoading) return <p className="p-8">Confirming your order...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load order: {error.message}</p>

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold text-green-600">Payment Successful</h1>
      <p className="mt-2 text-gray-600">Order status: {order.status}</p>
      <p className="text-gray-600">Total: ${order.total}</p>

      <div className="flex flex-col gap-3 mt-6">
        {order.items.map((item) => (
          <div key={item.product_id} className="border-b pb-2">
            <p className="font-medium">{item.product_name}</p>
            <p className="text-sm text-gray-500">
              Qty {item.quantity} × ${item.unit_price}
            </p>
          </div>
        ))}
      </div>

      <Link to="/products" className="text-blue-600 underline mt-6 inline-block">
        Continue shopping
      </Link>
    </div>
  )
}

export default OrderSuccess