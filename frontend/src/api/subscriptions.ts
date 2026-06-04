import client from './client'

export const createSubscription = (data: { document_id?: number; project_id?: number }) =>
  client.post('/subscriptions', data)

export const listSubscriptions = () =>
  client.get('/subscriptions')

export const deleteSubscription = (subId: number) =>
  client.delete(`/subscriptions/${subId}`)

export const listNotifications = (params?: { page?: number; page_size?: number }) =>
  client.get('/notifications', { params })

export const markNotificationRead = (notifId: number) =>
  client.put(`/notifications/${notifId}/read`)

export const markAllNotificationsRead = () =>
  client.put('/notifications/read-all')
