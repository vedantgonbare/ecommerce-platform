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
    <div className="max-w-sm mx-auto mt-16 px-6">
      <h1 className="font-display text-2xl text-ink mb-6">Register</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="border border-line rounded-xs p-2 text-ink"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="border border-line rounded-xs p-2 text-ink"
        />
        <button
          type="submit"
          disabled={registerMutation.isPending}
          className="bg-tan text-ink rounded-xs p-2 font-semibold disabled:opacity-50"
        >
          {registerMutation.isPending ? 'Registering...' : 'Register'}
        </button>
        {registerMutation.error && (
          <p className="text-red-600 text-sm">{registerMutation.error.message}</p>
        )}
      </form>
      <p className="mt-4 text-sm text-ink-muted">
        Already have an account? <Link to="/login" className="text-ink underline">Log in</Link>
      </p>
    </div>
  )
}

export default Register