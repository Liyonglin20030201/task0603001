import { useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Button, Space, Spin } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

interface Props {
  url: string
}

export default function PdfViewer({ url }: Props) {
  const [numPages, setNumPages] = useState(0)
  const [pageNumber, setPageNumber] = useState(1)
  const [loading, setLoading] = useState(true)

  return (
    <div style={{ textAlign: 'center' }}>
      <Document
        file={url}
        onLoadSuccess={({ numPages }) => { setNumPages(numPages); setLoading(false) }}
        onLoadError={() => setLoading(false)}
        loading={<Spin size="large" style={{ margin: '50px auto', display: 'block' }} />}
      >
        <Page pageNumber={pageNumber} width={700} />
      </Document>
      {!loading && numPages > 0 && (
        <Space style={{ marginTop: 16 }}>
          <Button icon={<LeftOutlined />} disabled={pageNumber <= 1} onClick={() => setPageNumber(pageNumber - 1)} />
          <span>{pageNumber} / {numPages}</span>
          <Button icon={<RightOutlined />} disabled={pageNumber >= numPages} onClick={() => setPageNumber(pageNumber + 1)} />
        </Space>
      )}
      {!loading && numPages === 0 && (
        <div style={{ padding: 40, color: '#999' }}>预览不可用（文件未转换为PDF）</div>
      )}
    </div>
  )
}
