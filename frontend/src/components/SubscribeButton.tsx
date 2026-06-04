import { useState, useEffect } from 'react'
import { Button, message } from 'antd'
import { BellOutlined, BellFilled } from '@ant-design/icons'
import { createSubscription, listSubscriptions, deleteSubscription } from '../api/subscriptions'
import { Subscription } from '../types'

interface Props {
  documentId?: number
  projectId?: number
}

export default function SubscribeButton({ documentId, projectId }: Props) {
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    listSubscriptions().then(({ data }) => {
      const match = (data as Subscription[]).find(
        (s) => (documentId && s.document_id === documentId) || (projectId && s.project_id === projectId)
      )
      setSubscription(match || null)
    })
  }, [documentId, projectId])

  const handleToggle = async () => {
    setLoading(true)
    try {
      if (subscription) {
        await deleteSubscription(subscription.id)
        setSubscription(null)
        message.success('已取消订阅')
      } else {
        const payload: any = {}
        if (documentId) payload.document_id = documentId
        if (projectId) payload.project_id = projectId
        const { data } = await createSubscription(payload)
        setSubscription(data)
        message.success('已订阅')
      }
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button
      icon={subscription ? <BellFilled /> : <BellOutlined />}
      type={subscription ? 'primary' : 'default'}
      onClick={handleToggle}
      loading={loading}
    >
      {subscription ? '已订阅' : '订阅'}
    </Button>
  )
}
