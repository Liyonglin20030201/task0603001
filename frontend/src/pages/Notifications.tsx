import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { List, Button, Tag, Typography, Space, Badge, message, Card, Empty, Popconfirm } from 'antd'
import { CheckOutlined, CheckCircleOutlined, BellOutlined, DeleteOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listNotifications, markNotificationRead, markAllNotificationsRead, deleteNotification } from '../api/subscriptions'
import { Notification, NotificationListResponse } from '../types'

export default function Notifications() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [total, setTotal] = useState(0)
  const [unreadCount, setUnreadCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  const fetchData = async (p = page) => {
    setLoading(true)
    try {
      const { data } = await listNotifications({ page: p, page_size: 20 })
      const resp = data as NotificationListResponse
      setNotifications(resp.items)
      setTotal(resp.total)
      setUnreadCount(resp.unread_count)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const handleMarkRead = async (id: number) => {
    await markNotificationRead(id)
    fetchData(page)
  }

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead()
    message.success('已全部标记为已读')
    fetchData(page)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteNotification(id)
      message.success('已删除')
      fetchData(page)
    } catch {
      message.error('删除失败')
    }
  }

  const eventTypeLabel = (type: string) => {
    switch (type) {
      case 'new_version': return <Tag color="blue">新版本</Tag>
      case 'document_restored': return <Tag color="green">文档恢复</Tag>
      case 'new_comment': return <Tag color="orange">新评论</Tag>
      default: return <Tag>{type}</Tag>
    }
  }

  return (
    <div>
      <Space style={{ marginBottom: 16, justifyContent: 'space-between', width: '100%', display: 'flex' }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          <BellOutlined style={{ marginRight: 8 }} />
          通知中心
          {unreadCount > 0 && <Badge count={unreadCount} style={{ marginLeft: 8 }} />}
        </Typography.Title>
        {unreadCount > 0 && (
          <Button icon={<CheckCircleOutlined />} onClick={handleMarkAllRead}>
            全部标记已读
          </Button>
        )}
      </Space>

      {notifications.length === 0 && !loading ? (
        <Empty description="暂无通知" />
      ) : (
        <List
          loading={loading}
          dataSource={notifications}
          pagination={{
            current: page,
            total,
            pageSize: 20,
            onChange: (p) => { setPage(p); fetchData(p) },
          }}
          renderItem={(item) => (
            <Card
              size="small"
              style={{
                marginBottom: 8,
                backgroundColor: item.is_read ? '#fff' : '#f0f5ff',
                borderLeft: item.is_read ? undefined : '3px solid #1890ff',
              }}
            >
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space>
                  {eventTypeLabel(item.event_type)}
                  <span>{item.message}</span>
                  {item.document_id && (
                    <a onClick={() => navigate(`/documents/${item.document_id}`)}>
                      查看文档
                    </a>
                  )}
                </Space>
                <Space>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {dayjs(item.created_at).format('MM-DD HH:mm')}
                  </Typography.Text>
                  {!item.is_read && (
                    <Button
                      type="link"
                      size="small"
                      icon={<CheckOutlined />}
                      onClick={() => handleMarkRead(item.id)}
                    >
                      标记已读
                    </Button>
                  )}
                  <Popconfirm title="确认删除此通知?" onConfirm={() => handleDelete(item.id)}>
                    <Button
                      type="link"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                    >
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              </Space>
            </Card>
          )}
        />
      )}
    </div>
  )
}
