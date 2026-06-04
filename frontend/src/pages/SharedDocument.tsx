import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Typography, Spin, Input, Button, Form, message, Descriptions, Tag, Result } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { accessSharedDocument, verifySharedDocument } from '../api/shares'
import { SharedDocument } from '../types'

export default function SharedDocumentPage() {
  const { token } = useParams<{ token: string }>()
  const [doc, setDoc] = useState<SharedDocument | null>(null)
  const [loading, setLoading] = useState(true)
  const [needsPassword, setNeedsPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    if (!token) return
    accessSharedDocument(token)
      .then(({ data }) => { setDoc(data); setLoading(false) })
      .catch((e) => {
        const detail = e.response?.data?.detail || ''
        if (e.response?.status === 403 && detail.includes('Password')) {
          setNeedsPassword(true)
        } else {
          setError(detail || '链接无效或已过期')
        }
        setLoading(false)
      })
  }, [token])

  const handleVerify = async (values: { password: string }) => {
    if (!token) return
    setVerifying(true)
    try {
      const { data } = await verifySharedDocument(token, values.password)
      setDoc(data)
      setNeedsPassword(false)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '密码错误')
    } finally {
      setVerifying(false)
    }
  }

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />

  if (error) {
    return (
      <div style={{ maxWidth: 600, margin: '80px auto' }}>
        <Result status="warning" title="无法访问" subTitle={error} />
      </div>
    )
  }

  if (needsPassword) {
    return (
      <div style={{ maxWidth: 400, margin: '80px auto' }}>
        <Card title={<span><LockOutlined /> 此文档需要密码访问</span>}>
          <Form onFinish={handleVerify}>
            <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password placeholder="请输入访问密码" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={verifying} block>
                验证
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    )
  }

  if (!doc) return null

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: '0 24px' }}>
      <Card>
        <Typography.Title level={3}>{doc.title}</Typography.Title>
        <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
          <Descriptions.Item label="文件名">{doc.original_filename}</Descriptions.Item>
          <Descriptions.Item label="类型"><Tag>{doc.file_type.toUpperCase()}</Tag></Descriptions.Item>
          <Descriptions.Item label="版本">v{doc.current_version}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{dayjs(doc.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
        </Descriptions>
        {doc.summary && (
          <div style={{ marginBottom: 16 }}>
            <Typography.Title level={5}>摘要</Typography.Title>
            <Typography.Paragraph>{doc.summary}</Typography.Paragraph>
          </div>
        )}
        {doc.content && (
          <div>
            <Typography.Title level={5}>内容</Typography.Title>
            <div style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16, borderRadius: 4, maxHeight: 500, overflow: 'auto' }}>
              {doc.content}
            </div>
          </div>
        )}
      </Card>
      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Typography.Text type="secondary">此文档通过分享链接查看</Typography.Text>
      </div>
    </div>
  )
}
