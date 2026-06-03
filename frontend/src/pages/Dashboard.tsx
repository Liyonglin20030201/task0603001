import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Input, Select, DatePicker, Tag, Space, Button, Typography, Card, Row, Col, List } from 'antd'
import { SearchOutlined, ClockCircleOutlined, StarOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listDocuments } from '../api/documents'
import { listProjects } from '../api/projects'
import { listTags } from '../api/tags'
import { getQuickAccess } from '../api/favorites'
import { DocumentItem, Project, Tag as TagType, QuickAccessData } from '../types'

const { RangePicker } = DatePicker

export default function Dashboard() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [tags, setTags] = useState<TagType[]>([])
  const [filters, setFilters] = useState<Record<string, any>>({})
  const [quickAccess, setQuickAccess] = useState<QuickAccessData | null>(null)

  const fetchDocs = async (p = page, f = filters) => {
    setLoading(true)
    try {
      const { data } = await listDocuments({ page: p, page_size: 20, ...f })
      setDocuments(data.items)
      setTotal(data.total)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocs()
    listProjects().then((r) => setProjects(r.data))
    listTags().then((r) => setTags(r.data))
    getQuickAccess().then((r) => setQuickAccess(r.data))
  }, [])

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      render: (text: string, record: DocumentItem) => (
        <a onClick={() => navigate(`/documents/${record.id}`)}>{text}</a>
      ),
    },
    { title: '类型', dataIndex: 'file_type', width: 80 },
    {
      title: '标签',
      dataIndex: 'tags',
      render: (tags: TagType[]) => tags.map((t) => <Tag key={t.id}>{t.name}</Tag>),
    },
    { title: '版本', dataIndex: 'current_version', width: 70 },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
  ]

  const handleSearch = () => {
    setPage(1)
    fetchDocs(1, filters)
  }

  return (
    <div>
      {quickAccess && (quickAccess.recent.length > 0 || quickAccess.favorites.length > 0) && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          {quickAccess.recent.length > 0 && (
            <Col span={12}>
              <Card
                title={<span><ClockCircleOutlined style={{ marginRight: 8 }} />最近访问</span>}
                size="small"
              >
                <List
                  size="small"
                  dataSource={quickAccess.recent.slice(0, 5)}
                  renderItem={(item) => (
                    <List.Item style={{ padding: '4px 0' }}>
                      <a onClick={() => navigate(`/documents/${item.id}`)} style={{ flex: 1 }}>
                        {item.title}
                      </a>
                      <Tag style={{ marginLeft: 8 }}>{item.file_type.toUpperCase()}</Tag>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          )}
          {quickAccess.favorites.length > 0 && (
            <Col span={12}>
              <Card
                title={<span><StarOutlined style={{ marginRight: 8, color: '#faad14' }} />我的收藏</span>}
                size="small"
              >
                <List
                  size="small"
                  dataSource={quickAccess.favorites.slice(0, 5)}
                  renderItem={(item) => (
                    <List.Item style={{ padding: '4px 0' }}>
                      <a onClick={() => navigate(`/documents/${item.id}`)} style={{ flex: 1 }}>
                        {item.title}
                      </a>
                      <Tag style={{ marginLeft: 8 }}>{item.file_type.toUpperCase()}</Tag>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          )}
        </Row>
      )}

      <Typography.Title level={4}>文档列表</Typography.Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Select
          allowClear
          placeholder="按项目筛选"
          style={{ width: 160 }}
          onChange={(v) => setFilters({ ...filters, project_id: v })}
          options={projects.map((p) => ({ value: p.id, label: p.name }))}
        />
        <Select
          allowClear
          placeholder="按标签筛选"
          style={{ width: 160 }}
          onChange={(v) => setFilters({ ...filters, tag: v })}
          options={tags.map((t) => ({ value: t.name, label: t.name }))}
        />
        <RangePicker
          onChange={(dates) => {
            if (dates) {
              setFilters({
                ...filters,
                date_from: dates[0]?.toISOString(),
                date_to: dates[1]?.toISOString(),
              })
            } else {
              const { date_from, date_to, ...rest } = filters
              setFilters(rest)
            }
          }}
        />
        <Input
          placeholder="搜索标题"
          style={{ width: 200 }}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          onPressEnter={handleSearch}
        />
        <Button icon={<SearchOutlined />} type="primary" onClick={handleSearch}>
          搜索
        </Button>
      </Space>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={documents}
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: (p) => { setPage(p); fetchDocs(p, filters) },
        }}
      />
    </div>
  )
}
