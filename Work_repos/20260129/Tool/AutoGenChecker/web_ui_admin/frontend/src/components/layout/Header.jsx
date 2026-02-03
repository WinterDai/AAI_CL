import { Link, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import DeveloperSelector from '@/components/workflow/DeveloperSelector'

const navigation = [
  { name: 'Dashboard', href: '/' },
  { name: 'My Tasks', href: '/my-tasks' },
  { name: 'History', href: '/history' },
  { name: 'Modules', href: '/modules' },
  { name: 'Dispatch', href: '/dispatch' },
  { name: 'Collection', href: '/collection' },
  { name: 'Settings', href: '/settings' },
]

export default function Header() {
  const location = useLocation()

  return (
    <header className="h-10 border-b border-gray-200 bg-white">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center space-x-6">
          <Link to="/" className="text-sm font-semibold text-gray-900">
            AutoGenChecker
          </Link>

          {/* Navigation */}
          <nav className="flex items-center space-x-4">
            {navigation.map((item) => {
              const isActive = item.href === '/' 
                ? location.pathname === '/'
                : location.pathname.startsWith(item.href)
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    'text-xs font-medium transition-colors',
                    isActive
                      ? 'text-primary'
                      : 'text-gray-600 hover:text-gray-900'
                  )}
                >
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Right Actions */}
        <div className="flex items-center space-x-3">
          <DeveloperSelector />
          <button
            className="text-xs text-gray-600 hover:text-gray-900"
            title="Help"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  )
}
