import { useState, useEffect } from 'react'
import { Table, Button, Select, Form, message, Popconfirm, InputNumber } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { listPermissions, grantPermission, revokePermission } from '../api/permissions'
import { listUsers } from '../api/users'
import { DocumentPermission, User } from '../types'

interface Props {
  docId: number
}

export default function PermissionPanel({ docId }: Props) {
  const [permissions, setPermissions] = useState<DocumentPermission[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [form] = Form.useForm()

  const fetch = async () => {
    try {
      const [pRes, uRes] = await Promise.all([
        listPermissions(docId),
        listUsers().catch(() => ({ data: [] })),
      ])
      setPermissions(pRes.data)
      setUsers(uRes.data)
    } catch {}
  }

  useEffect(() => { fetch() }, [docId])

  const handleGrant = async (values: { user_id: number; permission_level: string }) => {
    try {
      await grantPermission(docId, values)
      message.success('权限已设置')
      form.resetFields()
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '设置失败')
    }
  }

  const handleRevoke = async (permissionId: number) => {
    try {
      await revokePermission(docId, permissionId)
      message.success('权限已撤销')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '撤销失败')
    }
  }

  const levelLabels: Record<string, string> = { read: '只读', write: '读写', admin: '管理' }

  const columns = [
    {
      title: '用户',
      dataIndex: 'user_id',
      render: (id: number) => users.find((u) => u.id === id)?.username || `用户 ${id}`,
    },
    {
      title: '权限级别',
      dataIndex: 'permission_level',
      render: (l: string) => levelLabels[l] || l,
    },
    {
      title: '操作',
      render: (_: any, record: DocumentPermission) => (
        <Popconfirm title="撤销此权限?" onConfirm={() => handleRevoke(record.id)}>
          <Button danger size="small">撤销</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <Form form={form} layout="inline" onFinish={handleGrant} style={{ marginBottom: 16 }}>
        <Form.Item name="user_id" rules={[{ required: true, message: '选择用户' }]}>
          <Select placeholder="选择用户" style={{ width: 160 }} options={users.map((u) => ({ value: u.id, label: u.username }))} />
        </Form.Item>
        <Form.Item name="permission_level" rules={[{ required: true, message: '选择权限' }]}>
          <Select placeholder="权限级别" style={{ width: 120 }} options={[
            { value: 'read', label: '只读' },
            { value: 'write', label: '读写' },
            { value: 'admin', label: '管理' },
          ]} />
        </Form.Item>
        <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>添加</Button>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={permissions} pagination={false} />
      <p style={{ color: '#888', marginTop: 8 }}>
        设置文档权限后，只有被授权的用户和文档所有者可以访问此文档。未设置权限时按系统角色控制。
      </p>
    </div>
  )
}
