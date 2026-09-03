import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

function ProductDetail() {
  const { id } = useParams()

  const {
    data: product,
    isLoading: productLoading,
    error: productError,
  } = useQuery({
    queryKey: ['product', id],
    queryFn: () => api.get(`/products/${id}`),
  })

  const { data: reviews, isLoading: reviewsLoading } = useQuery({
    queryKey: ['reviews', id],
    queryFn: () => api.get(`/products/${id}/reviews`),
  })

    if (productLoading) return <p className="p-8">Loading product...</p>
  if (productError) return <p className="p-8 text-red-600">Failed to load product: {productError.message}</p>

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold">{product.name}</h1>
      <p className="text-xl text-gray-600 mt-2">${product.price}</p>
      <p className="text-sm text-gray-400 mt-1">
        {product.stock_quantity > 0
          ? `${product.stock_quantity} in stock`
          : 'Out of stock'}
      </p>
      {product.description && (
        <p className="mt-4 text-gray-700">{product.description}</p>
      )}

      <h2 className="text-lg font-semibold mt-8 mb-2">Reviews</h2>
      {reviewsLoading ? (
        <p className="text-gray-400">Loading reviews...</p>
      ) : reviews.length === 0 ? (
        <p className="text-gray-400">No reviews yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {reviews.map((review) => (
            <div key={review.id} className="border-b pb-2">
              <p className="font-medium">{review.rating} / 5</p>
              {review.comment && <p className="text-gray-700">{review.comment}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProductDetail