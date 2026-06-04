import client from './client'

export const batchDelete = (document_ids: number[]) =>
  client.post('/documents/batch/delete', { document_ids })

export const batchMove = (document_ids: number[], project_id: number) =>
  client.post('/documents/batch/move', { document_ids, project_id })

export const batchAddTags = (document_ids: number[], tag_names: string[]) =>
  client.post('/documents/batch/tags', { document_ids, tag_names })

export const batchSetPermissions = (document_ids: number[], user_id: number, permission_level: string) =>
  client.post('/documents/batch/permissions', { document_ids, user_id, permission_level })
