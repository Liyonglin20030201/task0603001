import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Switch, DatePicker, InputNumber, Input, message, Typography, Tag, Space, Popconfirm } from 'antd'
import { CopyOutlined, LinkOutlined, DeleteOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { createShareLink, listShareLinks, deactivateShareLink } from '../api/shares'
import { ShareLink } from '../types'

interface Props {
  docId: number
  isOwnerOrAdmin: boolean
}

export default function SharePanel({ docId, isOwnerOrAdmin }: Props) {
  const [shares, setShares] = useState<ShareLink[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form] = Form.useForm()

  const fetchShares = async () => {
    if (!isOwnerOrAdmin) return
    setLoading(true)
    try {
      const { data } = await listShareLinks(docId)
      setShares(data)
    } catch {
      // may fail if not owner
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchShares() }, [docId])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      setCreating(true)
      const payload: any = {
        is_permanent: values.is_permanent || false,
      }
      if (!values.is_permanent) {
        if (!values.expires_at) {
          message.error('临时链接需要设置有效期')
          setCreating(false)
          return
        }
        payload.expires_at = values.expires_at.toISOString()
      }
      if (values.max_access_count) payload.max_access_count = values.max_access_count
      if (values.password) payload.password = values.password

      const { data } = await createShareLink(docId, payload)
      message.success('分享链接已创建')
      const shareUrl = `${window.location.origin}/shared/${data.token}`
      Modal.success({
        title: '分享链接',
        content: (
          <div>
            <Input value={shareUrl} readOnly style={{ marginBottom: 8 }} />
            <Button
              icon={<CopyOutlined />}
              onClick={() => { navigator.clipboard.writeText(shareUrl); message.success('已复制') }}
            >
              复制链接
            </Button>
          </div>
        ),
      })
      setModalOpen(false)
      form.resetFields()
      fetchShares()
    } catch (e: any) {
      if (e?.response?.data?.detail) message.error(e.response.data.detail)
    } finally {
      setCreating(false)
    }
  }

  const handleDeactivate = async (shareId: number) => {
    try {
      await deactivateShareLink(docId, shareId)
      message.success('链接已停用')
      fetchShares()
    } catch {
      message.error('操作失败')
    }
  }

  const columns = [
    {
      title: '链接Token',
      dataIndex: 'token',
      ellipsis: true,
      width: 200,
      render: (token: string) => (
        <Typography.Text copyable={{ text: `${window.location.origin}/shared/${token}` }}>
          {token.slice(0, 16)}...
        </Typography.Text>
      ),
    },
    {
      title: '类型',
      dataIndex: 'is_permanent',
      width: 80,
      render: (v: boolean) => v ? <Tag color="blue">永久</Tag> : <Tag color="orange">临时</Tag>,
    },
    {
      title: '有效期',
      dataIndex: 'expires_at',
      width: 160,
      render: (v: string | null) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '访问次数',
      width: 120,
      render: (_: any, r: ShareLink) =>
        r.max_access_count ? `${r.current_access_count}/${r.max_access_count}` : r.current_access_count,
    },
    {
      title: '密码',
      dataIndex: 'has_password',
      width: 60,
      render: (v: boolean) => v ? '有' : '无',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (v: boolean) => v ? <Tag color="green">有效</Tag> : <Tag color="red">已停用</Tag>,
    },
    {
      title: '操作',
      width: 80,
      render: (_: any, r: ShareLink) => r.is_active ? (
        <Popconfirm title="确认停用此链接?" onConfirm={() => handleDeactivate(r.id)}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>停用</Button>
        </Popconfirm>
      ) : null,
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<LinkOutlined />} onClick={() => setModalOpen(true)}>
          创建分享链接
        </Button>
      </Space>
      <Table
        rowKey="id"
        size="small"
        columns={columns}
        dataSource={shares}
        loading={loading}
        pagination={false}
      />

      <Modal
        title="创建分享链接"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        onOk={handleCreate}
        confirmLoading={creating}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" initialValues={{ is_permanent: false }}>
          <Form.Item name="is_permanent" label="永久链接" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.is_permanent !== cur.is_permanent}>
            {({ getFieldValue }) => !getFieldValue('is_permanent') && (
              <Form.Item name="expires_at" label="过期时间" rules={[{ required: true, message: '请选择过期时间' }]}>
                <DatePicker showTime style={{ width: '100%' }} disabledDate={(d) => d.isBefore(dayjs())} />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item name="max_access_count" label="最大访问次数（留空不限）">
            <InputNumber min={1} style={{ width: '100%' }} placeholder="不限" />
          </Form.Item>
          <Form.Item name="password" label="访问密码（留空不设密码）">
            <Input.Password placeholder="不设密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
