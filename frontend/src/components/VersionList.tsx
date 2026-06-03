import { useState, useEffect } from 'react'
import { Table, Button, Tag, message, Upload, Popconfirm } from 'antd'
import { UploadOutlined, RollbackOutlined, DownloadOutlined } from '@ant-design/icons'
import { listVersions, rollbackVersion, uploadVersion, getDownloadUrl } from '../api/documents'
import { DocumentVersion } from '../types'
import { useAuthStore } from '../store/authStore'
import dayjs from 'dayjs'

interface Props {
  docId: number
  currentVersion: number
  onRollback: () => void
}

export default function VersionList({ docId, currentVersion, onRollback }: Props) {
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [loading, setLoading] = useState(false)
  const user = useAuthStore((s) => s.user)

  const fetch = async () => {
    const { data } = await listVersions(docId)
    setVersions(data)
  }

  useEffect(() => { fetch() }, [docId])

  const handleRollback = async (versionNumber: number) => {
    setLoading(true)
    try {
      await rollbackVersion(docId, versionNumber)
      message.success(`已回退到 v${versionNumber}`)
      fetch()
      onRollback()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '回退失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUploadVersion = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    try {
      await uploadVersion(docId, formData)
      message.success('新版本已上传')
      fetch()
      onRollback()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '上传失败')
    }
    return false
  }

  const columns = [
    {
      title: '版本',
      dataIndex: 'version_number',
      render: (v: number) => (
        <>v{v} {v === currentVersion && <Tag color="green">当前</Tag>}</>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      render: (s: number) => `${(s / 1024).toFixed(1)} KB`,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      render: (_: any, record: DocumentVersion) => (
        <>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            href={getDownloadUrl(docId, record.version_number)}
            style={{ marginRight: 8 }}
          >
            下载
          </Button>
          {record.version_number !== currentVersion && user?.role !== 'viewer' && (
            <Popconfirm title={`确定回退到 v${record.version_number}?`} onConfirm={() => handleRollback(record.version_number)}>
              <Button size="small" icon={<RollbackOutlined />} loading={loading}>
                回退
              </Button>
            </Popconfirm>
          )}
        </>
      ),
    },
  ]

  return (
    <div>
      {user?.role !== 'viewer' && (
        <Upload beforeUpload={handleUploadVersion} showUploadList={false} maxCount={1}>
          <Button icon={<UploadOutlined />} style={{ marginBottom: 16 }}>上传新版本</Button>
        </Upload>
      )}
      <Table rowKey="id" columns={columns} dataSource={versions} pagination={false} />
    </div>
  )
}
