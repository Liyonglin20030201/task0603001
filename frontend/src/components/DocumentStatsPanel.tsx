import { useState, useEffect } from 'react'
import { Table, Typography, Spin, Statistic, Row, Col, Card } from 'antd'
import { EyeOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { getDocumentStats } from '../api/statistics'
import { DocumentStats } from '../types'

interface Props {
  docId: number
}

export default function DocumentStatsPanel({ docId }: Props) {
  const [stats, setStats] = useState<DocumentStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDocumentStats(docId)
      .then(({ data }) => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [docId])

  if (loading) return <Spin />
  if (!stats) return <Typography.Text type="secondary">暂无统计数据</Typography.Text>

  const accessColumns = [
    { title: '用户', dataIndex: 'username' },
    {
      title: '访问时间',
      dataIndex: 'accessed_at',
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
  ]

  const versionColumns = [
    { title: '版本', dataIndex: 'version_number', width: 70 },
    { title: '上传者', dataIndex: 'uploader_username', render: (v: string | null) => v || '-' },
    { title: '文件大小', dataIndex: 'file_size', width: 100, render: (v: number) => `${(v / 1024).toFixed(1)} KB` },
    { title: '时间', dataIndex: 'created_at', render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm') },
  ]

  return (
    <div>
      <Row style={{ marginBottom: 16 }}>
        <Col>
          <Statistic title="总访问次数" value={stats.total_accesses} prefix={<EyeOutlined />} />
        </Col>
      </Row>

      <Typography.Title level={5}>访问记录</Typography.Title>
      <Table
        rowKey={(r, i) => `${r.user_id}-${i}`}
        size="small"
        columns={accessColumns}
        dataSource={stats.access_records}
        pagination={{ pageSize: 10 }}
        style={{ marginBottom: 24 }}
      />

      <Typography.Title level={5}>版本更新历史</Typography.Title>
      <Table
        rowKey="version_number"
        size="small"
        columns={versionColumns}
        dataSource={stats.version_history}
        pagination={false}
      />
    </div>
  )
}
