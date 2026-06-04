import client from './client'

export const getSystemStats = () =>
  client.get('/statistics/system')

export const getDocumentStats = (docId: number, params?: { page?: number; page_size?: number }) =>
  client.get(`/statistics/documents/${docId}`, { params })
