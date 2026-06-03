import { Typography, Tag } from 'antd'
import { DiffLine, DiffStats } from '../types'

interface Props {
  diffLines: DiffLine[]
  stats: DiffStats
}

const lineStyle: React.CSSProperties = {
  fontFamily: 'monospace',
  fontSize: 13,
  padding: '2px 8px',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-all',
  borderBottom: '1px solid #f0f0f0',
  minHeight: 24,
  lineHeight: '22px',
}

const lineNumStyle: React.CSSProperties = {
  width: 40,
  minWidth: 40,
  textAlign: 'right',
  padding: '2px 6px',
  color: '#999',
  fontSize: 12,
  borderRight: '1px solid #e8e8e8',
  borderBottom: '1px solid #f0f0f0',
  userSelect: 'none',
  fontFamily: 'monospace',
}

const bgColors: Record<string, { left: string; right: string }> = {
  equal: { left: '#fff', right: '#fff' },
  add: { left: '#f8f8f8', right: '#e6ffed' },
  delete: { left: '#ffeef0', right: '#f8f8f8' },
  change: { left: '#ffeef0', right: '#e6ffed' },
}

export default function DiffViewer({ diffLines, stats }: Props) {
  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
        <Tag color="green">+{stats.additions} 新增</Tag>
        <Tag color="red">-{stats.deletions} 删除</Tag>
        <Tag color="orange">~{stats.changes} 修改</Tag>
        <Typography.Text type="secondary">共 {stats.total_lines} 行</Typography.Text>
      </div>

      <div style={{ border: '1px solid #e8e8e8', borderRadius: 6, overflow: 'hidden' }}>
        <div style={{ display: 'flex', borderBottom: '2px solid #e8e8e8' }}>
          <div style={{ flex: 1, padding: '8px 12px', background: '#fafafa', fontWeight: 500, textAlign: 'center' }}>
            旧版本
          </div>
          <div style={{ width: 1, background: '#e8e8e8' }} />
          <div style={{ flex: 1, padding: '8px 12px', background: '#fafafa', fontWeight: 500, textAlign: 'center' }}>
            新版本
          </div>
        </div>

        <div style={{ maxHeight: 600, overflowY: 'auto' }}>
          {diffLines.map((line, idx) => (
            <div key={idx} style={{ display: 'flex' }}>
              <div style={{ ...lineNumStyle, background: bgColors[line.type].left }}>
                {line.line_left ?? ''}
              </div>
              <div style={{ ...lineStyle, flex: 1, background: bgColors[line.type].left }}>
                {line.content_left}
              </div>
              <div style={{ width: 1, background: '#e8e8e8' }} />
              <div style={{ ...lineNumStyle, background: bgColors[line.type].right }}>
                {line.line_right ?? ''}
              </div>
              <div style={{ ...lineStyle, flex: 1, background: bgColors[line.type].right }}>
                {line.content_right}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
