import { useState, useEffect } from 'react'
import { Table, Button, message, Typography } from 'antd'
import { listTrash, restoreDocument } from '../api/documents'
import { DocumentItem } from '../types'
import dayjs from 'dayjs'

export default function Trash() {
  const [docs, setDocs] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(false)

  const fetch = async () => {
    setLoading(true)
    try {
      const { data } = await listTrash()
      setDocs(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch() }, [])

  const handleRestore = async (id: number) => {
    try {
      await restoreDocument(id)
      message.success('恢复成功')
      fetch()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '恢复失败')
    }
  }

  const columns = [
    { title: '标题', dataIndex: 'title' },
    { title: '文件名', dataIndex: 'original_filename' },
    { title: '类型', dataIndex: 'file_type' },
    { title: '删除时间', dataIndex: 'created_at', render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm') },
    {
      title: '操作',
      render: (_: any, record: DocumentItem) => (
        <Button type="primary" size="small" onClick={() => handleRestore(record.id)}>
          恢复
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Typography.Title level={4}>回收站</Typography.Title>
      <Table rowKey="id" columns={columns} dataSource={docs} loading={loading} />
    </div>
  )
}
