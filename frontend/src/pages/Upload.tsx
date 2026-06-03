import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload as AntUpload, Form, Input, Select, Button, message, Card } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { uploadDocument } from '../api/documents'
import { listProjects } from '../api/projects'
import { Project } from '../types'

const { Dragger } = AntUpload

export default function Upload() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])

  useEffect(() => {
    listProjects().then((r) => setProjects(r.data))
  }, [])

  const onFinish = async (values: { title: string; project_id?: number }) => {
    if (!file) {
      message.warning('请选择文件')
      return
    }
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', values.title)
      if (values.project_id) formData.append('project_id', String(values.project_id))
      const { data } = await uploadDocument(formData)
      message.success('上传成功')
      navigate(`/documents/${data.id}`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '上传失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="上传文档" style={{ maxWidth: 600, margin: '0 auto' }}>
      <Form layout="vertical" onFinish={onFinish}>
        <Form.Item label="文件">
          <Dragger
            accept=".pdf,.docx,.pptx,.doc,.ppt,.xlsx,.xls,.txt,.md"
            maxCount={1}
            beforeUpload={(f) => { setFile(f); return false }}
            onRemove={() => setFile(null)}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p>点击或拖拽文件到此区域上传</p>
            <p style={{ color: '#888' }}>支持 PDF, Word, PPT, Excel, TXT, Markdown</p>
          </Dragger>
        </Form.Item>
        <Form.Item name="title" label="文档标题" rules={[{ required: true, message: '请输入标题' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="project_id" label="所属项目">
          <Select allowClear placeholder="选择项目" options={projects.map((p) => ({ value: p.id, label: p.name }))} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            上传
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}
