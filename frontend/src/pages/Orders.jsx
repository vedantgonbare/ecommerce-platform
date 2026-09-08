import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

function Orders() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['orders'],
    queryFn: () => api.get('/orders/?limit=20&offset=0'),
  })

  if (isLoading) return <p className="p-8">Loading orders...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load orders: {error.message}</p>
    return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold mb-4">Your Orders</h1>

      {data.items.length === 0 ? (
        <p className="text-gray-400">You haven't placed any orders yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {data.items.map((order) => (
            <Link
              key={order.id}
              to={`/orders/${order.id}`}
              className="border rounded p-4 hover:shadow flex justify-between items-center"
            >
              <div>
                <p className="font-medium">Order #{order.id.slice(0, 8)}</p>
                <p className="text-sm text-gray-500">
                  {new Date(order.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="text-right">
                <p className="font-medium">${order.total}</p>
                <p className="text-sm text-gray-500 capitalize">{order.status}</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default Orders