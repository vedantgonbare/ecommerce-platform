import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'

function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const loginMutation = useMutation({
    mutationFn: (credentials) => api.post('/auth/login', credentials),
    onSuccess: () => {
      navigate('/')
    },
  })

  function handleSubmit(e) {
    e.preventDefault()
    loginMutation.mutate({ email, password })
  }

  return (
    <div className="max-w-sm mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-4">Login</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="border border-gray-300 rounded p-2"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="border border-gray-300 rounded p-2"
        />

        {loginMutation.isError && (
          <p className="text-red-600 text-sm">{loginMutation.error.message}</p>
        )}

        <button
          type="submit"
          disabled={loginMutation.isPending}
          className="bg-blue-600 text-white rounded p-2 disabled:opacity-50"
        >
          {loginMutation.isPending ? 'Logging in...' : 'Log In'}
        </button>
      </form>
    </div>
  )
}

export default Login