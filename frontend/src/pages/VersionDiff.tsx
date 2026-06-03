import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Typography, Spin, Button, message } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { compareVersions } from '../api/documents'
import { VersionDiffResponse } from '../types'
import DiffViewer from '../components/DiffViewer'

export default function VersionDiff() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [diffData, setDiffData] = useState<VersionDiffResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const v1 = Number(searchParams.get('v1'))
  const v2 = Number(searchParams.get('v2'))

  useEffect(() => {
    if (!id || !v1 || !v2) return
    setLoading(true)
    compareVersions(Number(id), v1, v2)
      .then(({ data }) => setDiffData(data))
      .catch((e: any) => message.error(e.response?.data?.detail || '获取对比数据失败'))
      .finally(() => setLoading(false))
  }, [id, v1, v2])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/documents/${id}`)}>
          返回文档
        </Button>
        <Typography.Title level={4} style={{ margin: 0 }}>
          版本对比: v{v1} vs v{v2}
        </Typography.Title>
      </div>

      {diffData ? (
        <DiffViewer diffLines={diffData.diff_lines} stats={diffData.stats} />
      ) : (
        <Typography.Text type="danger">无法获取对比数据</Typography.Text>
      )}
    </div>
  )
}
