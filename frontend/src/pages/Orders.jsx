import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const LIMIT = 20

function Orders() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = Number(searchParams.get('page')) || 1
  const offset = (page - 1) * LIMIT

  const { data, isLoading, error } = useQuery({
    queryKey: ['orders', page],
    queryFn: () => api.get(`/orders/?limit=${LIMIT}&offset=${offset}`),
  })

  function goToPage(newPage) {
    setSearchParams({ page: String(newPage) })
  }

  if (isLoading) return <p className="p-8">Loading orders...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load orders: {error.message}</p>

  const totalPages = Math.ceil(data.total / LIMIT)

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="font-display text-2xl text-ink mb-4">Your Orders</h1>

      {data.items.length === 0 ? (
        <p className="text-ink-muted">You haven't placed any orders yet.</p>
      ) : (
        <>
          <div className="flex flex-col gap-3">
            {data.items.map((order) => (
              <Link
                key={order.id}
                to={`/orders/${order.id}`}
                className="border border-line rounded-xs p-4 hover:shadow flex justify-between items-center"
              >
                <div>
                  <p className="font-medium text-ink">Order #{order.id.slice(0, 8)}</p>
                  <p className="text-sm text-ink-muted">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-ink">${order.total}</p>
                  <p className="text-sm text-ink-muted capitalize">{order.status}</p>
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="mt-6 flex justify-center gap-2">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                <button
                  key={n}
                  onClick={() => goToPage(n)}
                  disabled={n === page}
                  className={`px-3 py-1 rounded-xs border border-line ${
                    n === page ? 'bg-tan text-ink font-semibold' : 'text-ink hover:bg-surface'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Orders