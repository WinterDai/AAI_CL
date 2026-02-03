import { Outlet } from 'react-router-dom'
import Header from './Header'

export default function MainLayout() {
  return (
    <div className="h-full flex flex-col">
      <Header />
      <main className="flex-1 overflow-auto custom-scrollbar">
        <Outlet />
      </main>
    </div>
  )
}
