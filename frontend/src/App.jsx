import { Routes, Route, Link } from 'react-router-dom'
import Login from './pages/Login'

function Home() {
  return <h1>Home Page</h1>
}

function App() {
  return (
    <div className="p-8">
      <nav className="flex gap-4 mb-6">
        <Link to="/" className="text-blue-600 underline">Home</Link>
        <Link to="/login" className="text-blue-600 underline">Login</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </div>
  )
}

export default App