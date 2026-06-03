import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Tabs, Typography, Descriptions, Tag, Spin, message } from 'antd'
import { getDocument, getPreviewUrl } from '../api/documents'
import { DocumentItem } from '../types'
import VersionList from '../components/VersionList'
import CommentList from '../components/CommentList'
import PermissionPanel from '../components/PermissionPanel'
import PdfViewer from '../components/PdfViewer'
import { useAuthStore } from '../store/authStore'
import dayjs from 'dayjs'

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>()
  const [doc, setDoc] = useState<DocumentItem | null>(null)
  const [loading, setLoading] = useState(true)
  const user = useAuthStore((s) => s.user)

  const fetchDoc = async () => {
    try {
      const { data } = await getDocument(Number(id))
      setDoc(data)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '获取文档失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDoc() }, [id])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!doc) return <Typography.Text type="danger">文档不存在</Typography.Text>

  const isOwnerOrAdmin = user?.role === 'admin' || user?.id === doc.owner_id

  const tabItems = [
    {
      key: 'preview',
      label: '在线预览',
      children: <PdfViewer url={getPreviewUrl(doc.id)} />,
    },
    {
      key: 'comments',
      label: '备注',
      children: <CommentList docId={doc.id} />,
    },
    {
      key: 'versions',
      label: '版本记录',
      children: <VersionList docId={doc.id} currentVersion={doc.current_version} onRollback={fetchDoc} />,
    },
    ...(isOwnerOrAdmin
      ? [{
          key: 'permissions',
          label: '权限管理',
          children: <PermissionPanel docId={doc.id} />,
        }]
      : []),
  ]

  return (
    <div>
      <Typography.Title level={4}>{doc.title}</Typography.Title>
      <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="文件名">{doc.original_filename}</Descriptions.Item>
        <Descriptions.Item label="类型">{doc.file_type.toUpperCase()}</Descriptions.Item>
        <Descriptions.Item label="当前版本">v{doc.current_version}</Descriptions.Item>
        <Descriptions.Item label="创建时间">{dayjs(doc.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
        <Descriptions.Item label="标签" span={2}>
          {doc.tags.map((t) => <Tag key={t.id} color="blue">{t.name}</Tag>)}
        </Descriptions.Item>
        {doc.summary && (
          <Descriptions.Item label="摘要" span={2}>
            {doc.summary}
          </Descriptions.Item>
        )}
      </Descriptions>
      <Tabs items={tabItems} />
    </div>
  )
}
