import { Navigate, Route, Routes } from 'react-router-dom'
import { CenterPage, DemoPage, ResultsPage, SocialPage } from './pages/Pages'

export default function App() {
  return (
    <Routes>
      <Route path="/red" element={<SocialPage />} />
      <Route path="/centro" element={<CenterPage />} />
      <Route path="/demo" element={<DemoPage />} />
      <Route path="/resultados" element={<ResultsPage />} />
      <Route path="*" element={<Navigate to="/demo" replace />} />
    </Routes>
  )
}
