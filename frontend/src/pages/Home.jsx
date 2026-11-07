import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import ProductImage from '../components/ProductImage'

const TILE_COLORS = ['bg-tile-lavender', 'bg-tile-peach', 'bg-tile-pink', 'bg-tile-blue']

function Home() {
  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.get('/categories'),
  })

  const { data: featuredData, isLoading: productsLoading } = useQuery({
    queryKey: ['products', 'featured'],
    queryFn: () => api.get('/products/?limit=3'),
  })

  return (
    <div>
      {/* Hero */}
      <section className="relative">
        <div
          className="h-105 bg-cover bg-center flex items-center"
          style={{
            backgroundImage:
              "url('https://plus.unsplash.com/premium_photo-1664201890375-f8fa405cdb7d?w=1600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D')",
          }}
        >
          <div className="mx-auto max-w-6xl px-6 w-full">
            <h1 className="font-display text-4xl sm:text-5xl text-white font-bold max-w-xl">
              Driftline
            </h1>
            <p className="mt-3 text-white/90 max-w-md">
              Everyday essentials, thoughtfully picked.
            </p>
            <Link
              to="/products"
              className="inline-block mt-6 bg-tan text-ink px-6 py-3 rounded-xs font-semibold"
            >
              Shop Now
            </Link>
          </div>
        </div>

        {/* Trust strip — overlaps hero bottom edge */}
        <div className="mx-auto max-w-5xl px-6 -mt-10 relative">
          <div className="bg-white border border-line rounded-xs shadow-md grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-line">
            <div className="p-5 text-center">
              <p className="font-semibold text-ink">Secure checkout (Stripe)</p>
            </div>
            <div className="p-5 text-center">
              <p className="font-semibold text-ink">Live stock levels</p>
            </div>
            <div className="p-5 text-center">
              <p className="font-semibold text-ink">Verified reviews</p>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="font-display text-2xl text-ink mb-6">Shop by Category</h2>
        {categoriesLoading ? (
          <p className="text-ink-muted">Loading categories...</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {categories.map((category, i) => (
              <Link
                key={category.id}
                to={`/products?category_id=${category.id}`}
                className={`${TILE_COLORS[i % TILE_COLORS.length]} rounded-xs p-6 flex items-center justify-center text-center font-semibold text-ink min-h-25`}
              >
                {category.name}
              </Link>
            ))}
          </div>
        )}
      </section>    

      {/* Featured products */}
      <section className="mx-auto max-w-6xl px-6 py-16 bg-surface">
        <h2 className="font-display text-2xl text-ink mb-6">Featured Products</h2>
        {productsLoading ? (
          <p className="text-ink-muted">Loading products...</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {featuredData.items.map((product) => (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="block bg-white rounded-xs overflow-hidden border border-line"
              >
                <ProductImage src={product.image_url} alt={product.name} />
                <div className="p-4">
                  <p className="font-semibold text-ink">{product.name}</p>
                  <p className="text-ink-muted">${product.price}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-line py-8">
        <div className="mx-auto max-w-6xl px-6 text-center text-ink-muted text-sm">
          © {new Date().getFullYear()} Driftline
        </div>
      </footer>
    </div>
  )
}

export default Home