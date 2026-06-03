import { useState, useEffect } from 'react'
import { Button, Tooltip, message } from 'antd'
import { StarOutlined, StarFilled } from '@ant-design/icons'
import { getFavoriteStatus, addFavorite, removeFavorite } from '../api/favorites'

interface Props {
  documentId: number
  onToggle?: (isFavorited: boolean) => void
}

export default function FavoriteButton({ documentId, onToggle }: Props) {
  const [isFavorited, setIsFavorited] = useState(false)
  const [favoriteId, setFavoriteId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getFavoriteStatus(documentId).then(({ data }) => {
      setIsFavorited(data.is_favorited)
      setFavoriteId(data.favorite_id)
    })
  }, [documentId])

  const handleToggle = async () => {
    setLoading(true)
    try {
      if (isFavorited && favoriteId) {
        await removeFavorite(favoriteId)
        setIsFavorited(false)
        setFavoriteId(null)
        message.success('已取消收藏')
      } else {
        const { data } = await addFavorite({ document_id: documentId })
        setIsFavorited(true)
        setFavoriteId(data.id)
        message.success('已添加收藏')
      }
      onToggle?.(!isFavorited)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Tooltip title={isFavorited ? '取消收藏' : '添加收藏'}>
      <Button
        type="text"
        icon={isFavorited ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
        onClick={handleToggle}
        loading={loading}
      />
    </Tooltip>
  )
}
