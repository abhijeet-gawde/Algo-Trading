async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || 'The local API could not complete the request.')
  }
  return body
}

export const getSession = () => request('/session')
export const getProfile = () => request('/profile')
export const logout = () => request('/logout', { method: 'POST' })
export const login = (credentials) => request('/login', {
  method: 'POST',
  body: JSON.stringify(credentials),
})