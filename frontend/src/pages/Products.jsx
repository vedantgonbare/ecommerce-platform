import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import ProductImage from '../components/ProductImage'

function Products() {
  const [searchParams] = useSearchParams()
  const categoryId = searchParams.get('category_id')

  const { data, isLoading, error } = useQuery({
    queryKey: ['products', categoryId],
    queryFn: () => {
      const params = new URLSearchParams({ limit: '12', offset: '0' })
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

  if (isLoading) return <p className="p-8">Loading products...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load products: {error.message}</p>

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="mb-2 font-display text-3xl">Products</h1>

      {categoryId && (
        <p className="mb-6 text-ink-muted">
          Filtered by: <span className="font-semibold text-ink">{activeCategory?.name ?? '...'}</span>
          {' · '}
          <Link to="/products" className="underline">Clear filter</Link>
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
              <h2 className="font-semibold">{product.name}</h2>
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
    </div>
  )
}

export default Products