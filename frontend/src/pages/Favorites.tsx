import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Typography, Card, List, Button, Modal, Input, Menu, Empty, message, Popconfirm, Tag, Space,
} from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined, FolderOutlined, AppstoreOutlined } from '@ant-design/icons'
import {
  listFavorites, listFavoriteCategories, createFavoriteCategory,
  updateFavoriteCategory, deleteFavoriteCategory, removeFavorite,
  moveFavoriteCategory,
} from '../api/favorites'
import { Favorite, FavoriteCategory } from '../types'
import dayjs from 'dayjs'

export default function Favorites() {
  const navigate = useNavigate()
  const [favorites, setFavorites] = useState<Favorite[]>([])
  const [categories, setCategories] = useState<FavoriteCategory[]>([])
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingCategory, setEditingCategory] = useState<FavoriteCategory | null>(null)
  const [categoryName, setCategoryName] = useState('')

  const fetchCategories = async () => {
    const { data } = await listFavoriteCategories()
    setCategories(data)
  }

  const fetchFavorites = async (categoryId: number | null = selectedCategory) => {
    setLoading(true)
    try {
      const params: any = {}
      if (categoryId !== null) {
        params.category_id = categoryId
      }
      const { data } = await listFavorites(params)
      setFavorites(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCategories()
    fetchFavorites()
  }, [])

  const handleCategorySelect = (key: string) => {
    const catId = key === 'all' ? null : Number(key)
    setSelectedCategory(catId)
    fetchFavorites(catId)
  }

  const handleCreateOrUpdateCategory = async () => {
    if (!categoryName.trim()) return
    try {
      if (editingCategory) {
        await updateFavoriteCategory(editingCategory.id, categoryName.trim())
        message.success('分类已更新')
      } else {
        await createFavoriteCategory(categoryName.trim())
        message.success('分类已创建')
      }
      setModalVisible(false)
      setCategoryName('')
      setEditingCategory(null)
      fetchCategories()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '操作失败')
    }
  }

  const handleDeleteCategory = async (id: number) => {
    await deleteFavoriteCategory(id)
    message.success('分类已删除')
    fetchCategories()
    if (selectedCategory === id) {
      setSelectedCategory(null)
      fetchFavorites(null)
    }
  }

  const handleRemoveFavorite = async (favoriteId: number) => {
    await removeFavorite(favoriteId)
    message.success('已取消收藏')
    fetchFavorites()
    fetchCategories()
  }

  const handleMoveCategory = async (favoriteId: number, categoryId: number | null) => {
    await moveFavoriteCategory(favoriteId, categoryId)
    message.success('已移动')
    fetchFavorites()
    fetchCategories()
  }

  const menuItems = [
    { key: 'all', icon: <AppstoreOutlined />, label: '全部收藏' },
    { key: '0', icon: <FolderOutlined />, label: '未分类' },
    ...categories.map((c) => ({
      key: String(c.id),
      icon: <FolderOutlined />,
      label: (
        <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{c.name} ({c.count})</span>
          <span onClick={(e) => e.stopPropagation()}>
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => { setEditingCategory(c); setCategoryName(c.name); setModalVisible(true) }}
            />
            <Popconfirm title="删除此分类？收藏项将变为未分类" onConfirm={() => handleDeleteCategory(c.id)}>
              <Button type="text" size="small" icon={<DeleteOutlined />} danger />
            </Popconfirm>
          </span>
        </span>
      ),
    })),
  ]

  return (
    <div>
      <Typography.Title level={4}>我的收藏</Typography.Title>
      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ width: 240, flexShrink: 0 }}>
          <Button
            icon={<PlusOutlined />}
            style={{ width: '100%', marginBottom: 12 }}
            onClick={() => { setEditingCategory(null); setCategoryName(''); setModalVisible(true) }}
          >
            新建分类
          </Button>
          <Menu
            mode="inline"
            selectedKeys={[selectedCategory === null ? 'all' : String(selectedCategory)]}
            items={menuItems}
            onClick={({ key }) => handleCategorySelect(key)}
          />
        </div>
        <div style={{ flex: 1 }}>
          {favorites.length === 0 && !loading ? (
            <Empty description="暂无收藏" />
          ) : (
            <List
              loading={loading}
              dataSource={favorites}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      size="small"
                      type="link"
                      onClick={() => navigate(`/documents/${item.document_id}`)}
                    >
                      查看
                    </Button>,
                    <Popconfirm title="取消收藏？" onConfirm={() => handleRemoveFavorite(item.id)}>
                      <Button size="small" type="link" danger>取消收藏</Button>
                    </Popconfirm>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <a onClick={() => navigate(`/documents/${item.document_id}`)}>
                        {item.document.title}
                      </a>
                    }
                    description={
                      <Space>
                        <Tag>{item.document.file_type.toUpperCase()}</Tag>
                        {item.document.tags.map((t) => <Tag key={t.id} color="blue">{t.name}</Tag>)}
                        <span style={{ color: '#999', fontSize: 12 }}>
                          收藏于 {dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
                        </span>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </div>
      </div>

      <Modal
        title={editingCategory ? '编辑分类' : '新建分类'}
        open={modalVisible}
        onOk={handleCreateOrUpdateCategory}
        onCancel={() => { setModalVisible(false); setCategoryName(''); setEditingCategory(null) }}
      >
        <Input
          placeholder="分类名称"
          value={categoryName}
          onChange={(e) => setCategoryName(e.target.value)}
          onPressEnter={handleCreateOrUpdateCategory}
        />
      </Modal>
    </div>
  )
}
