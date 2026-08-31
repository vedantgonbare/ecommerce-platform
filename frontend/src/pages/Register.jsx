import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'

function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const registerMutation = useMutation({
    mutationFn: (credentials) => api.post('/auth/register', credentials),
    onSuccess: () => {
      navigate('/login')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    registerMutation.mutate({ email, password })
  }
  return (
    <div className="p-8 max-w-sm mx-auto">
      <h1 className="text-2xl mb-4">Register</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="border p-2 rounded"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="border p-2 rounded"
        />
        <button
          type="submit"
          disabled={registerMutation.isPending}
          className="bg-blue-600 text-white p-2 rounded disabled:opacity-50"
        >
          {registerMutation.isPending ? 'Registering...' : 'Register'}
        </button>
        {registerMutation.error && (
          <p className="text-red-600 text-sm">{registerMutation.error.message}</p>
        )}
      </form>
      <p className="mt-4 text-sm">
        Already have an account? <Link to="/login" className="text-blue-600 underline">Log in</Link>
      </p>
    </div>
  )
}

export default Register
