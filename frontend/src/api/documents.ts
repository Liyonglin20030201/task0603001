import client from './client'

export const listDocuments = (params: Record<string, any>) =>
  client.get('/documents', { params })

export const getDocument = (id: number) =>
  client.get(`/documents/${id}`)

export const uploadDocument = (formData: FormData) =>
  client.post('/documents', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

export const updateDocument = (id: number, data: { title?: string; project_id?: number }) =>
  client.put(`/documents/${id}`, data)

export const deleteDocument = (id: number) =>
  client.delete(`/documents/${id}`)

export const restoreDocument = (id: number) =>
  client.post(`/documents/${id}/restore`)

export const listTrash = () =>
  client.get('/documents/trash')

export const listVersions = (docId: number) =>
  client.get(`/documents/${docId}/versions`)

export const uploadVersion = (docId: number, formData: FormData) =>
  client.post(`/documents/${docId}/versions`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })

export const rollbackVersion = (docId: number, versionNumber: number) =>
  client.post(`/documents/${docId}/versions/${versionNumber}/rollback`)

export const getPreviewUrl = (docId: number) =>
  `/api/documents/${docId}/preview`

export const getDownloadUrl = (docId: number, versionNumber: number) =>
  `/api/documents/${docId}/versions/${versionNumber}/download`
