import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, Typography, Spin } from 'antd'
import { FileTextOutlined, EyeOutlined, UserOutlined, FireOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { getSystemStats } from '../api/statistics'
import { SystemStats } from '../types'

export default function Statistics() {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSystemStats()
      .then(({ data }) => setStats(data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!stats) return null

  const popularColumns = [
    { title: '排名', width: 60, render: (_: any, __: any, i: number) => i + 1 },
    { title: '文档标题', dataIndex: 'title', ellipsis: true },
    { title: '访问次数', dataIndex: 'access_count', width: 100 },
  ]

  const activeColumns = [
    { title: '排名', width: 60, render: (_: any, __: any, i: number) => i + 1 },
    { title: '用户名', dataIndex: 'username' },
    { title: '访问次数', dataIndex: 'access_count', width: 100 },
  ]

  return (
    <div>
      <Typography.Title level={4}>系统统计</Typography.Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="文档总数" value={stats.total_documents} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总访问量" value={stats.total_visits} prefix={<EyeOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="活跃用户数" value={stats.total_users} prefix={<UserOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title={<span><FireOutlined style={{ marginRight: 8, color: '#f5222d' }} />热门文档 Top 10</span>}>
            <Table
              rowKey="document_id"
              size="small"
              columns={popularColumns}
              dataSource={stats.popular_documents}
              pagination={false}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title={<span><UserOutlined style={{ marginRight: 8, color: '#1890ff' }} />活跃用户 Top 10</span>}>
            <Table
              rowKey="user_id"
              size="small"
              columns={activeColumns}
              dataSource={stats.active_users}
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
