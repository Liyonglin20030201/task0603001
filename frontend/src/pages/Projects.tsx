import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, Space, message, Typography, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { listProjects, createProject, updateProject, deleteProject, addMember, removeMember } from '../api/projects'
import { listUsers } from '../api/users'
import { Project, User } from '../types'
import { useAuthStore } from '../store/authStore'
import SubscribeButton from '../components/SubscribeButton'

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [memberModalOpen, setMemberModalOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [memberForm] = Form.useForm()
  const currentUser = useAuthStore((s) => s.user)

  const fetch = async () => {
    setLoading(true)
    try {
      const [pRes, uRes] = await Promise.all([listProjects(), listUsers().catch(() => ({ data: [] }))])
      setProjects(pRes.data)
      setUsers(uRes.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch() }, [])

  const getUserName = (userId: number) => {
    const u = users.find((u) => u.id === userId)
    return u ? u.username : `用户${userId}`
  }

  const handleCreate = async (values: { name: string; description?: string }) => {
    try {
      await createProject(values)
      message.success('创建成功')
      setModalOpen(false)
      form.resetFields()
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '创建失败')
    }
  }

  const handleEdit = async (values: { name: string; description?: string }) => {
    if (!selectedProject) return
    try {
      await updateProject(selectedProject.id, values)
      message.success('更新成功')
      setEditModalOpen(false)
      editForm.resetFields()
      setSelectedProject(null)
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '更新失败')
    }
  }

  const openEditModal = (project: Project) => {
    setSelectedProject(project)
    editForm.setFieldsValue({ name: project.name, description: project.description || '' })
    setEditModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteProject(id)
      message.success('删除成功')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '删除失败')
    }
  }

  const handleAddMember = async (values: { user_id: number; role: string }) => {
    if (!selectedProject) return
    try {
      await addMember(selectedProject.id, values)
      message.success('添加成功')
      memberForm.resetFields()
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '添加失败')
    }
  }

  const handleRemoveMember = async (projectId: number, userId: number) => {
    try {
      await removeMember(projectId, userId)
      message.success('移除成功')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '移除失败')
    }
  }

  const columns = [
    { title: '项目名', dataIndex: 'name' },
    { title: '描述', dataIndex: 'description' },
    {
      title: '成员',
      render: (_: any, record: Project) => (
        <Button size="small" onClick={() => { setSelectedProject(record); setMemberModalOpen(true) }}>
          管理成员 ({record.members?.length || 0})
        </Button>
      ),
    },
    {
      title: '操作',
      render: (_: any, record: Project) => (
        <Space>
          <SubscribeButton projectId={record.id} />
          {(currentUser?.role === 'admin' || currentUser?.id === record.owner_id) && (
            <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)}>编辑</Button>
          )}
          {currentUser?.role === 'admin' && (
            <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
              <Button danger size="small">删除</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>项目管理</Typography.Title>
        {currentUser?.role !== 'viewer' && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            新建项目
          </Button>
        )}
      </Space>
      <Table rowKey="id" columns={columns} dataSource={projects} loading={loading} />

      <Modal title="新建项目" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="项目名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑项目"
        open={editModalOpen}
        onCancel={() => { setEditModalOpen(false); editForm.resetFields() }}
        onOk={() => editForm.submit()}
        okText="保存"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical" onFinish={handleEdit}>
          <Form.Item name="name" label="项目名" rules={[{ required: true, message: '请输入项目名' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`成员管理 - ${selectedProject?.name}`}
        open={memberModalOpen}
        onCancel={() => setMemberModalOpen(false)}
        footer={null}
        width={600}
      >
        {selectedProject && (
          <>
            <Table
              rowKey="id"
              size="small"
              dataSource={selectedProject.members}
              columns={[
                {
                  title: '用户',
                  dataIndex: 'user_id',
                  render: (userId: number) => getUserName(userId),
                },
                { title: '角色', dataIndex: 'role', render: (v: string) => v === 'lead' ? '负责人' : '成员' },
                {
                  title: '操作',
                  render: (_, m) => (
                    <Button danger size="small" onClick={() => handleRemoveMember(selectedProject.id, m.user_id)}>
                      移除
                    </Button>
                  ),
                },
              ]}
            />
            <Form form={memberForm} layout="inline" onFinish={handleAddMember} style={{ marginTop: 16 }}>
              <Form.Item name="user_id" rules={[{ required: true }]}>
                <Select placeholder="选择用户" style={{ width: 160 }} options={users.map((u) => ({ value: u.id, label: u.username }))} />
              </Form.Item>
              <Form.Item name="role" initialValue="member">
                <Select style={{ width: 100 }} options={[{ value: 'member', label: '成员' }, { value: 'lead', label: '负责人' }]} />
              </Form.Item>
              <Button type="primary" htmlType="submit">添加</Button>
            </Form>
          </>
        )}
      </Modal>
    </div>
  )
}
