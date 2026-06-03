import client from './client'

export const searchDocuments = (params: { q: string; page?: number; page_size?: number }) =>
  client.get('/search', { params })
