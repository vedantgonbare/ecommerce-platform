import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import ProductImage from '../components/ProductImage'

function Products() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: () => api.get('/products/?limit=12&offset=0'),
  })

  if (isLoading) return <p className="p-8">Loading products...</p>
  if (error) return <p className="p-8 text-red-600">Failed to load products: {error.message}</p>

  return (
    <div className="p-8">
      <h1 className="text-2xl mb-4">Products</h1>
      <div className="grid grid-cols-3 gap-4">
        {data.items.map((product) => (
          <Link
            key={product.id}
            to={`/products/${product.id}`}
            className="block border border-line bg-white hover:shadow-md"
          >
            <ProductImage src={product.image_url} alt={product.name} />
            <div className="p-4">
            <h2 className="font-semibold">{product.name}</h2>
            <p className="text-ink-mute">${product.price}</p>
            <p className="text-sum text-ink-muted">
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