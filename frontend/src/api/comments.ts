import client from './client'

export const listComments = (docId: number) =>
  client.get(`/documents/${docId}/comments`)

export const createComment = (docId: number, content: string) =>
  client.post(`/documents/${docId}/comments`, { content })

export const updateComment = (docId: number, commentId: number, content: string) =>
  client.put(`/documents/${docId}/comments/${commentId}`, { content })

export const deleteComment = (docId: number, commentId: number) =>
  client.delete(`/documents/${docId}/comments/${commentId}`)
