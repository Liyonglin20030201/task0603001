export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
  is_active: boolean
  created_at: string
}

export interface Tag {
  id: number
  name: string
}

export interface DocumentItem {
  id: number
  title: string
  original_filename: string
  file_type: string
  summary: string | null
  project_id: number | null
  owner_id: number
  current_version: number
  is_deleted: boolean
  created_at: string
  updated_at: string | null
  tags: Tag[]
}

export interface DocumentListResponse {
  items: DocumentItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface DocumentVersion {
  id: number
  version_number: number
  file_size: number
  uploaded_by: number | null
  created_at: string
}

export interface Comment {
  id: number
  document_id: number
  user_id: number
  content: string
  created_at: string
  updated_at: string | null
}

export interface Project {
  id: number
  name: string
  description: string | null
  created_by: number | null
  owner_id: number | null
  created_at: string
  members: ProjectMember[]
}

export interface ProjectMember {
  id: number
  project_id: number
  user_id: number
  role: string
  joined_at: string
}

export interface DocumentPermission {
  id: number
  document_id: number
  user_id: number
  permission_level: string
  granted_at: string
  granted_by: number | null
}
