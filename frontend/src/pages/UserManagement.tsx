import { useState, useEffect } from 'react'
import { Table, Select, Switch, message, Typography } from 'antd'
import { listUsers, updateUserRole, updateUserActive } from '../api/users'
import { User } from '../types'

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)

  const fetch = async () => {
    setLoading(true)
    try {
      const { data } = await listUsers()
      setUsers(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch() }, [])

  const handleRoleChange = async (userId: number, role: string) => {
    try {
      await updateUserRole(userId, role)
      message.success('角色已更新')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '更新失败')
    }
  }

  const handleActiveChange = async (userId: number, active: boolean) => {
    try {
      await updateUserActive(userId, active)
      message.success(active ? '已激活' : '已停用')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '更新失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '用户名', dataIndex: 'username' },
    { title: '邮箱', dataIndex: 'email' },
    {
      title: '角色',
      dataIndex: 'role',
      render: (role: string, record: User) => (
        <Select
          value={role}
          onChange={(v) => handleRoleChange(record.id, v)}
          style={{ width: 100 }}
          options={[
            { value: 'admin', label: '管理员' },
            { value: 'editor', label: '编辑者' },
            { value: 'viewer', label: '查看者' },
          ]}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      render: (active: boolean, record: User) => (
        <Switch checked={active} onChange={(v) => handleActiveChange(record.id, v)} />
      ),
    },
  ]

  return (
    <div>
      <Typography.Title level={4}>用户管理</Typography.Title>
      <Table rowKey="id" columns={columns} dataSource={users} loading={loading} />
    </div>
  )
}
