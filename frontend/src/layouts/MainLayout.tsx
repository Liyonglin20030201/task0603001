import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Typography, Badge } from 'antd'
import {
  FileTextOutlined,
  UploadOutlined,
  ProjectOutlined,
  DeleteOutlined,
  UserOutlined,
  LogoutOutlined,
  SearchOutlined,
  StarOutlined,
  BellOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { useState, useEffect } from 'react'
import { listNotifications } from '../api/subscriptions'

const { Sider, Header, Content } = Layout

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    listNotifications({ page: 1, page_size: 1 })
      .then(({ data }) => setUnreadCount(data.unread_count))
      .catch(() => {})
  }, [location.pathname])

  const menuItems = [
    { key: '/', icon: <FileTextOutlined />, label: '文档列表' },
    { key: '/search', icon: <SearchOutlined />, label: '全文搜索' },
    { key: '/favorites', icon: <StarOutlined />, label: '我的收藏' },
    { key: '/notifications', icon: <BellOutlined />, label: unreadCount > 0 ? `通知 (${unreadCount})` : '通知' },
    ...(user?.role !== 'viewer'
      ? [{ key: '/upload', icon: <UploadOutlined />, label: '上传文档' }]
      : []),
    { key: '/projects', icon: <ProjectOutlined />, label: '项目管理' },
    ...(user?.role === 'admin'
      ? [
          { key: '/admin/statistics', icon: <BarChartOutlined />, label: '系统统计' },
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
