import client from './client'

export const listUsers = () => client.get('/users')

export const updateUserRole = (userId: number, role: string) =>
  client.put(`/users/${userId}/role`, { role })

export const updateUserActive = (userId: number, is_active: boolean) =>
  client.put(`/users/${userId}/active`, { is_active })
