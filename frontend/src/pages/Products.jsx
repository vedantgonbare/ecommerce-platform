import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import ProductImage from '../components/ProductImage'

const LIMIT = 12

function Products() {
  const [searchParams, setSearchParams] = useSearchParams()
  const categoryId = searchParams.get('category_id')
  const page = Number(searchParams.get('page')) || 1
  const offset = (page - 1) * LIMIT

  const { data, isLoading, error } = useQuery({
    queryKey: ['products', categoryId, page],
    queryFn: () => {
      const params = new URLSearchParams({ limit: String(LIMIT), offset: String(offset) })
      if (categoryId) params.set('category_id', categoryId)
      return api.get(`/products/?${params.toString()}`)
    },
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.get('/categories'),
    enabled: !!categoryId,
  })

  const activeCategory = categories?.find((c) => c.id === categoryId)

  function goToPage(newPage) {
    const next = new URLSearchParams(searchParams)
    next.set('page', String(newPage))
    setSearchParams(next)
  }

  function clearFilter() {
    setSearchParams({})
  }

  if (isLoading) return <p className="p-8">Loading products...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load products: {error.message}</p>

  const totalPages = Math.ceil(data.total / LIMIT)

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="mb-2 font-display text-3xl text-ink">Products</h1>

      {categoryId && (
        <p className="mb-6 text-ink-muted">
          Filtered by: <span className="font-semibold text-ink">{activeCategory?.name ?? '...'}</span>
          {' · '}
          <button onClick={clearFilter} className="underline">Clear filter</button>
        </p>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {data.items.map((product) => (
          <Link
            key={product.id}
            to={`/products/${product.id}`}
            className="block border border-line bg-white hover:shadow-md"
          >
            <ProductImage src={product.image_url} alt={product.name} />
            <div className="p-4">
              <h2 className="font-semibold text-ink">{product.name}</h2>
              <p className="text-ink-muted">${product.price}</p>
              <p className="text-sm text-ink-muted">
                {product.stock_quantity > 0
                  ? `${product.stock_quantity} in stock`
                  : 'Out of stock'}
              </p>
            </div>
          </Link>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-8 flex justify-center gap-2">
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
    </div>
  )
}

export default Products