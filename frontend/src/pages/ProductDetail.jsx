import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

function ProductDetail() {
  const { id } = useParams()
  const queryClient = useQueryClient()

  const addToCart = useMutation({
    mutationFn: () => api.post('/cart/items', { product_id: id, quantity: 1 }),
    onSuccess: (data) => {
      queryClient.setQueryData(['cart'], data)
    },
  })

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

      <div className="mt-6">
        <button
          onClick={() => addToCart.mutate()}
          disabled={addToCart.isPending || product.stock_quantity === 0}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {addToCart.isPending ? 'Adding...' : 'Add to Cart'}
        </button>
        {addToCart.error && (
          <p className="text-red-600 text-sm mt-2">{addToCart.error.message}</p>
        )}
      </div>
    </div>
  )
}

export default ProductDetail