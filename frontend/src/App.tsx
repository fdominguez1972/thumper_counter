import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import DeerGallery from './pages/DeerGallery'
import DeerDetail from './pages/DeerDetail'
import Images from './pages/Images'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/deer" element={<DeerGallery />} />
          <Route path="/deer/:id" element={<DeerDetail />} />
          <Route path="/images" element={<Images />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
