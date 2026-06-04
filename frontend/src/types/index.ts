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

export interface SearchResultItem {
  id: number
  title: string
  file_type: string
  title_highlight: string
  summary_highlight: string
  content_highlight: string
  relevance: number
  tags: string[]
  created_at: string
}

export interface SearchResponse {
  items: SearchResultItem[]
  query: string
  total: number
  page: number
  page_size: number
}

export interface FavoriteCategory {
  id: number
  name: string
  created_at: string
  count: number
}

export interface Favorite {
  id: number
  document_id: number
  category_id: number | null
  created_at: string
  document: DocumentItem
}

export interface FavoriteStatus {
  is_favorited: boolean
  favorite_id: number | null
  category_id: number | null
}

export interface QuickAccessData {
  recent: DocumentItem[]
  favorites: DocumentItem[]
}

export interface DiffLine {
  type: 'equal' | 'add' | 'delete' | 'change'
  line_left: number | null
  line_right: number | null
  content_left: string
  content_right: string
}

export interface DiffStats {
  additions: number
  deletions: number
  changes: number
  total_lines: number
}

export interface VersionDiffResponse {
  document_id: number
  version_left: number
  version_right: number
  diff_lines: DiffLine[]
  stats: DiffStats
}

export interface ShareLink {
  id: number
  document_id: number
  token: string
  is_permanent: boolean
  expires_at: string | null
  max_access_count: number | null
  current_access_count: number
  has_password: boolean
  is_active: boolean
  created_at: string
}

export interface SharedDocument {
  id: number
  title: string
  original_filename: string
  file_type: string
  summary: string | null
  content: string | null
  current_version: number
  created_at: string
}

export interface BatchResult {
  total: number
  succeeded: number
  failed: number
  errors: { document_id: number; error: string }[]
}

export interface Subscription {
  id: number
  user_id: number
  document_id: number | null
  project_id: number | null
  created_at: string
}

export interface Notification {
  id: number
  event_type: string
  document_id: number | null
  actor_id: number | null
  message: string
  is_read: boolean
  created_at: string
}

export interface NotificationListResponse {
  items: Notification[]
  total: number
  unread_count: number
}

export interface SystemStats {
  total_documents: number
  total_visits: number
  total_users: number
  popular_documents: { document_id: number; title: string; access_count: number }[]
  active_users: { user_id: number; username: string; access_count: number }[]
}

export interface DocumentStats {
  document_id: number
  total_accesses: number
  access_records: { user_id: number; username: string; accessed_at: string }[]
  version_history: { version_number: number; uploaded_by: number | null; uploader_username: string | null; file_size: number; created_at: string }[]
}
