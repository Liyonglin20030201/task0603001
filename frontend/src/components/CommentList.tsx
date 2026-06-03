import { useState, useEffect } from 'react'
import { List, Input, Button, message, Popconfirm, Space } from 'antd'
import { listComments, createComment, deleteComment } from '../api/comments'
import { Comment } from '../types'
import { useAuthStore } from '../store/authStore'
import dayjs from 'dayjs'

interface Props {
  docId: number
}

export default function CommentList({ docId }: Props) {
  const [comments, setComments] = useState<Comment[]>([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const user = useAuthStore((s) => s.user)

  const fetch = async () => {
    const { data } = await listComments(docId)
    setComments(data)
  }

  useEffect(() => { fetch() }, [docId])

  const handleSubmit = async () => {
    if (!content.trim()) return
    setLoading(true)
    try {
      await createComment(docId, content)
      setContent('')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '提交失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (commentId: number) => {
    try {
      await deleteComment(docId, commentId)
      message.success('已删除')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '删除失败')
    }
  }

  return (
    <div>
      <List
        dataSource={comments}
        renderItem={(item) => (
          <List.Item
            actions={
              (user?.id === item.user_id || user?.role === 'admin')
                ? [<Popconfirm title="删除?" onConfirm={() => handleDelete(item.id)}><a>删除</a></Popconfirm>]
                : []
            }
          >
            <List.Item.Meta
              title={`用户 ${item.user_id}`}
              description={dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
            />
            {item.content}
          </List.Item>
        )}
        locale={{ emptyText: '暂无备注' }}
      />
      <Space.Compact style={{ width: '100%', marginTop: 16 }}>
        <Input.TextArea
          rows={2}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="输入备注..."
        />
      </Space.Compact>
      <Button type="primary" onClick={handleSubmit} loading={loading} style={{ marginTop: 8 }}>
        提交备注
      </Button>
    </div>
  )
}
