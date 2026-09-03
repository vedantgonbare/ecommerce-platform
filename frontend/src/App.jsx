import { Routes, Route, Link } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import { useAuth } from './context/AuthContext'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'

function Home() {
  return <h1>Home Page</h1>
}

function App() {
    const { user, isLoading, logout } = useAuth()
  return (
    <div className="p-8">
      <nav className="flex gap-4 mb-6 items-center">
  <Link to="/" className="text-blue-600 underline">Home</Link>
  {isLoading ? (
    <span className="text-gray-400">Checking session...</span>
  ) : user ? (
    <>
      <span>Logged in as {user.email}</span>
      <button onClick={logout} className="text-blue-600 underline">Logout</button>
    </>
  ) : (
    <>
      <Link to="/login" className="text-blue-600 underline">Login</Link>
      <Link to="/register" className="text-blue-600 underline">Register</Link>
    </>
  )}
</nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/:id" element={<ProductDetail />} />
      </Routes>
    </div>
  )
}

export default App