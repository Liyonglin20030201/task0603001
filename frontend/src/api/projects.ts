import client from './client'

export const listProjects = () => client.get('/projects')

export const createProject = (data: { name: string; description?: string; owner_id?: number }) =>
  client.post('/projects', data)

export const updateProject = (id: number, data: { name?: string; description?: string; owner_id?: number }) =>
  client.put(`/projects/${id}`, data)

export const deleteProject = (id: number) => client.delete(`/projects/${id}`)

export const listMembers = (projectId: number) =>
  client.get(`/projects/${projectId}/members`)

export const addMember = (projectId: number, data: { user_id: number; role: string }) =>
  client.post(`/projects/${projectId}/members`, data)

export const removeMember = (projectId: number, userId: number) =>
  client.delete(`/projects/${projectId}/members/${userId}`)
