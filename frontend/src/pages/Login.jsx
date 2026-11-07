import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

function Login() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const loginMutation = useMutation({
    mutationFn: (credentials) => api.post('/auth/login', credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] })
      navigate('/')
    },
  })

  function handleSubmit(e) {
    e.preventDefault()
    loginMutation.mutate({ email, password })
  }

  return (
    <div className="max-w-sm mx-auto mt-16 px-6">
      <h1 className="font-display text-2xl text-ink mb-6">Login</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="border border-line rounded-[2px] p-2 text-ink"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="border border-line rounded-[2px] p-2 text-ink"
        />

        {loginMutation.isError && (
          <p className="text-red-600 text-sm">{loginMutation.error.message}</p>
        )}

        <button
          type="submit"
          disabled={loginMutation.isPending}
          className="bg-tan text-ink rounded-[2px] p-2 font-semibold disabled:opacity-50"
        >
          {loginMutation.isPending ? 'Logging in...' : 'Log In'}
        </button>
      </form>
    </div>
  )
}

export default Login