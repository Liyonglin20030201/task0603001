import client from './client'

export const addFavorite = (data: { document_id: number; category_id?: number }) =>
  client.post('/favorites', data)

export const removeFavorite = (favoriteId: number) =>
  client.delete(`/favorites/${favoriteId}`)

export const listFavorites = (params?: { category_id?: number }) =>
  client.get('/favorites', { params })

export const getFavoriteStatus = (documentId: number) =>
  client.get(`/favorites/status/${documentId}`)

export const listFavoriteCategories = () =>
  client.get('/favorites/categories')

export const createFavoriteCategory = (name: string) =>
  client.post('/favorites/categories', { name })

export const updateFavoriteCategory = (id: number, name: string) =>
  client.put(`/favorites/categories/${id}`, { name })

export const deleteFavoriteCategory = (id: number) =>
  client.delete(`/favorites/categories/${id}`)

export const moveFavoriteCategory = (favoriteId: number, categoryId: number | null) =>
  client.put(`/favorites/${favoriteId}/category`, { category_id: categoryId })

export const getQuickAccess = () =>
  client.get('/favorites/quick-access')
