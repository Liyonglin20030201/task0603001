import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Typography } from 'antd'
import {
  FileTextOutlined,
  UploadOutlined,
  ProjectOutlined,
  DeleteOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'

const { Sider, Header, Content } = Layout

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const menuItems = [
    { key: '/', icon: <FileTextOutlined />, label: '文档列表' },
    ...(user?.role !== 'viewer'
      ? [{ key: '/upload', icon: <UploadOutlined />, label: '上传文档' }]
      : []),
    { key: '/projects', icon: <ProjectOutlined />, label: '项目管理' },
    ...(user?.role === 'admin'
      ? [
          { key: '/trash', icon: <DeleteOutlined />, label: '回收站' },
          { key: '/admin/users', icon: <UserOutlined />, label: '用户管理' },
        ]
      : []),
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="dark">
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
            知识库
          </Typography.Title>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>欢迎, {user?.username} ({user?.role})</span>
          <Button
            icon={<LogoutOutlined />}
            onClick={() => { logout(); navigate('/login') }}
          >
            退出
          </Button>
        </Header>
        <Content style={{ margin: '24px', padding: '24px', background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
