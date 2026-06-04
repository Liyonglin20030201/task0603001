import client from './client'

export const createShareLink = (docId: number, data: {
  is_permanent: boolean
  expires_at?: string
  max_access_count?: number
  password?: string
}) => client.post(`/documents/${docId}/shares`, data)

export const listShareLinks = (docId: number) =>
  client.get(`/documents/${docId}/shares`)

export const deactivateShareLink = (docId: number, shareId: number) =>
  client.delete(`/documents/${docId}/shares/${shareId}`)

export const accessSharedDocument = (token: string) =>
  client.get(`/shared/${token}`)

export const verifySharedDocument = (token: string, password: string) =>
  client.post(`/shared/${token}/verify`, { password })
