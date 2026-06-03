import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Input, Card, Tag, Typography, Pagination, Spin, Empty, Space } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { searchDocuments } from '../api/search'
import { SearchResultItem } from '../types'

export default function Search() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const doSearch = async (q: string, p: number) => {
    if (!q.trim()) return
    setLoading(true)
    try {
      const { data } = await searchDocuments({ q: q.trim(), page: p, page_size: 20 })
      setResults(data.items)
      setTotal(data.total)
      setSearched(true)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value: string) => {
    setQuery(value)
    setPage(1)
    doSearch(value, 1)
  }

  const handlePageChange = (p: number) => {
    setPage(p)
    doSearch(query, p)
  }

  return (
    <div>
      <Typography.Title level={4}>全文搜索</Typography.Title>
      <Input.Search
        placeholder="搜索文档标题、摘要、标签、内容..."
        enterButton="搜索"
        size="large"
        style={{ maxWidth: 600, marginBottom: 24 }}
        onSearch={handleSearch}
        allowClear
      />

      {loading && <Spin size="large" style={{ display: 'block', margin: '60px auto' }} />}

      {!loading && searched && results.length === 0 && (
        <Empty description="未找到相关文档" style={{ marginTop: 60 }} />
      )}

      {!loading && results.length > 0 && (
        <div>
          <Typography.Text type="secondary" style={{ marginBottom: 16, display: 'block' }}>
            找到 {total} 个相关结果
          </Typography.Text>
          <Space direction="vertical" style={{ width: '100%' }} size={12}>
            {results.map((item) => (
              <Card
                key={item.id}
                hoverable
                size="small"
                onClick={() => navigate(`/documents/${item.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <FileTextOutlined style={{ color: '#1890ff' }} />
                  <span
                    style={{ fontSize: 16, fontWeight: 500 }}
                    dangerouslySetInnerHTML={{ __html: item.title_highlight }}
                  />
                  <Tag>{item.file_type.toUpperCase()}</Tag>
                </div>
                {item.summary_highlight && (
                  <div
                    style={{ color: '#666', fontSize: 13, marginBottom: 6 }}
                    dangerouslySetInnerHTML={{ __html: item.summary_highlight }}
                  />
                )}
                {item.content_highlight && (
                  <div
                    style={{ color: '#888', fontSize: 13, marginBottom: 8, fontStyle: 'italic' }}
                    dangerouslySetInnerHTML={{ __html: item.content_highlight }}
                  />
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    {item.tags.map((t) => (
                      <Tag key={t} color="blue">{t}</Tag>
                    ))}
                  </div>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
                  </Typography.Text>
                </div>
              </Card>
            ))}
          </Space>
          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <Pagination
              current={page}
              total={total}
              pageSize={20}
              onChange={handlePageChange}
              showSizeChanger={false}
            />
          </div>
        </div>
      )}
    </div>
  )
}
