const API_BASE_URL = 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    let errorDetail = 'Request failed'
    try {
      const errorBody = await response.json()
      errorDetail = errorBody.detail || errorDetail
    } catch {
      // response wasn't JSON, keep the generic message
    }
    throw new Error(errorDetail)
  }

  // Some endpoints (like logout) return a body; others may not.
  // Guard against trying to parse an empty response.
  const text = await response.text()
  return text ? JSON.parse(text) : null
}

export const api = {
  get: (path) => request(path, { method: 'GET' }),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),
}