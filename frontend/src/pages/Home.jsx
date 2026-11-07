import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

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
      <h1>Driftline — Home (shell)</h1>

      <section>
        <h2>Categories</h2>
        {categoriesLoading ? (
          <p>Loading categories...</p>
        ) : (
          <ul>
            {categories.map((category) => (
              <li key={category.id}>{category.name}</li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Featured Products</h2>
        {productsLoading ? (
          <p>Loading products...</p>
        ) : (
          <ul>
            {featuredData.items.map((product) => (
              <li key={product.id}>{product.name} — ${product.price}</li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

export default Home