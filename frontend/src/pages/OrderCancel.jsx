import { Link } from 'react-router-dom'

function OrderCancel() {
  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold text-red-600">Payment Cancelled</h1>
      <p className="mt-2 text-gray-600">
        Your payment was not completed. Your cart has been saved, so you can try again anytime.
      </p>

      <Link to="/cart" className="text-blue-600 underline mt-6 inline-block">
        Return to cart
      </Link>
    </div>
  )
}

export default OrderCancel