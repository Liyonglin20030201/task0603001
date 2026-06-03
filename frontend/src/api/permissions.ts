import client from './client'

export const listPermissions = (docId: number) =>
  client.get(`/documents/${docId}/permissions`)

export const grantPermission = (docId: number, data: { user_id: number; permission_level: string }) =>
  client.post(`/documents/${docId}/permissions`, data)

export const revokePermission = (docId: number, permissionId: number) =>
  client.delete(`/documents/${docId}/permissions/${permissionId}`)
