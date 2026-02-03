import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from '@/components/layout/MainLayout'
import Dashboard from '@/pages/Dashboard'
import Generator from '@/pages/Generator'
import History from '@/pages/History'
import Modules from '@/pages/Modules'
import Settings from '@/pages/Settings'
import Documentation from '@/pages/Documentation'
import MyTasks from '@/pages/MyTasks'
import Dispatch from '@/pages/Dispatch'
import Collection from '@/pages/Collection'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="my-tasks" element={<MyTasks />} />
        {/* 具体路径必须在动态路由 :itemId 之前 */}
        <Route path="generate/new" element={<Generator />} />
        <Route path="generate/step1" element={<Generator />} />
        <Route path="generate/step4" element={<Generator />} />
        <Route path="generate/step5" element={<Generator />} />
        <Route path="generate/:itemId" element={<Generator />} />
        <Route path="history" element={<History />} />
        <Route path="modules" element={<Modules />} />
        <Route path="dispatch" element={<Dispatch />} />
        <Route path="collection" element={<Collection />} />
        <Route path="settings" element={<Settings />} />
        <Route path="docs" element={<Documentation />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
