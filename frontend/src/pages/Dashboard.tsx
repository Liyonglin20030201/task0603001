import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Input, Select, DatePicker, Tag, Space, Button, Typography, Card, Row, Col, List, message, Modal, Popconfirm } from 'antd'
import { SearchOutlined, ClockCircleOutlined, StarOutlined, DeleteOutlined, FolderOutlined, TagsOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { listDocuments } from '../api/documents'
import { listProjects } from '../api/projects'
import { listTags } from '../api/tags'
import { getQuickAccess } from '../api/favorites'
import { batchDelete, batchMove, batchAddTags } from '../api/batch'
import { DocumentItem, Project, Tag as TagType, QuickAccessData } from '../types'
import { useAuthStore } from '../store/authStore'

const { RangePicker } = DatePicker

export default function Dashboard() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [tags, setTags] = useState<TagType[]>([])
  const [filters, setFilters] = useState<Record<string, any>>({})
  const [quickAccess, setQuickAccess] = useState<QuickAccessData | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [moveModalOpen, setMoveModalOpen] = useState(false)
  const [tagModalOpen, setTagModalOpen] = useState(false)
  const [moveProjectId, setMoveProjectId] = useState<number | null>(null)
  const [batchTagNames, setBatchTagNames] = useState<string[]>([])

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

  const handleBatchDelete = async () => {
    try {
      const { data } = await batchDelete(selectedIds)
      message.success(`成功删除 ${data.succeeded} 个文档${data.failed > 0 ? `，${data.failed} 个失败` : ''}`)
      setSelectedIds([])
      fetchDocs()
    } catch {
      message.error('批量删除失败')
    }
  }

  const handleBatchMove = async () => {
    if (!moveProjectId) { message.warning('请选择目标项目'); return }
    try {
      const { data } = await batchMove(selectedIds, moveProjectId)
      message.success(`成功移动 ${data.succeeded} 个文档${data.failed > 0 ? `，${data.failed} 个失败` : ''}`)
      setSelectedIds([])
      setMoveModalOpen(false)
      setMoveProjectId(null)
      fetchDocs()
    } catch {
      message.error('批量移动失败')
    }
  }

  const handleBatchTag = async () => {
    if (batchTagNames.length === 0) { message.warning('请输入标签'); return }
    try {
      const { data } = await batchAddTags(selectedIds, batchTagNames)
      message.success(`成功为 ${data.succeeded} 个文档添加标签${data.failed > 0 ? `，${data.failed} 个失败` : ''}`)
      setSelectedIds([])
      setTagModalOpen(false)
      setBatchTagNames([])
      fetchDocs()
    } catch {
      message.error('批量添加标签失败')
    }
  }

  const canBatch = user?.role !== 'viewer'

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

      {canBatch && selectedIds.length > 0 && (
        <div style={{ marginBottom: 12, padding: '8px 12px', background: '#e6f7ff', borderRadius: 4 }}>
          <Space>
            <span>已选择 {selectedIds.length} 个文档</span>
            <Popconfirm title={`确认删除 ${selectedIds.length} 个文档?`} onConfirm={handleBatchDelete}>
              <Button size="small" danger icon={<DeleteOutlined />}>批量删除</Button>
            </Popconfirm>
            <Button size="small" icon={<FolderOutlined />} onClick={() => setMoveModalOpen(true)}>批量移动</Button>
            <Button size="small" icon={<TagsOutlined />} onClick={() => setTagModalOpen(true)}>批量加标签</Button>
            <Button size="small" onClick={() => setSelectedIds([])}>取消选择</Button>
          </Space>
        </div>
      )}

      <Table
        rowKey="id"
        columns={columns}
        dataSource={documents}
        loading={loading}
        rowSelection={canBatch ? {
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        } : undefined}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: (p) => { setPage(p); fetchDocs(p, filters) },
        }}
      />

      <Modal
        title="批量移动到项目"
        open={moveModalOpen}
        onCancel={() => { setMoveModalOpen(false); setMoveProjectId(null) }}
        onOk={handleBatchMove}
        okText="移动"
        cancelText="取消"
      >
        <Select
          style={{ width: '100%' }}
          placeholder="选择目标项目"
          value={moveProjectId}
          onChange={setMoveProjectId}
          options={projects.map((p) => ({ value: p.id, label: p.name }))}
        />
      </Modal>

      <Modal
        title="批量添加标签"
        open={tagModalOpen}
        onCancel={() => { setTagModalOpen(false); setBatchTagNames([]) }}
        onOk={handleBatchTag}
        okText="添加"
        cancelText="取消"
      >
        <Select
          mode="tags"
          style={{ width: '100%' }}
          placeholder="输入标签名（可输入新标签）"
          value={batchTagNames}
          onChange={setBatchTagNames}
          options={tags.map((t) => ({ value: t.name, label: t.name }))}
        />
      </Modal>
    </div>
  )
}
