import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import DocumentDetail from './pages/DocumentDetail'
import Projects from './pages/Projects'
import Trash from './pages/Trash'
import UserManagement from './pages/UserManagement'
import Search from './pages/Search'
import Favorites from './pages/Favorites'
import VersionDiff from './pages/VersionDiff'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="upload" element={<Upload />} />
        <Route path="documents/:id" element={<DocumentDetail />} />
        <Route path="documents/:id/compare" element={<VersionDiff />} />
        <Route path="projects" element={<Projects />} />
        <Route path="search" element={<Search />} />
        <Route path="favorites" element={<Favorites />} />
        <Route path="trash" element={<Trash />} />
        <Route path="admin/users" element={<UserManagement />} />
      </Route>
    </Routes>
  )
}
