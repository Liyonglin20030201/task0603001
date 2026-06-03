import client from './client'

export const login = (username: string, password: string) =>
  client.post('/auth/login', { username, password })

export const register = (username: string, email: string, password: string) =>
  client.post('/auth/register', { username, email, password })

export const getMe = () => client.get('/auth/me')
