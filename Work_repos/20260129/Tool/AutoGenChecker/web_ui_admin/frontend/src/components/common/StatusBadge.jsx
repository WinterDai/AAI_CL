import clsx from 'clsx'

const statusStyles = {
  PASSED: 'bg-success text-white',
  FAILED: 'bg-error text-white',
  ERROR: 'bg-warning text-white',
  PENDING: 'bg-gray-200 text-gray-600',
  RUNNING: 'bg-primary/10 text-primary',
  COMPLETED: 'bg-green-100 text-green-800 border border-green-300',
  IN_PROGRESS: 'bg-blue-100 text-blue-800 border border-blue-300',
  'IN PROGRESS': 'bg-blue-100 text-blue-800 border border-blue-300',
  NOT_STARTED: 'bg-gray-100 text-gray-700 border border-gray-300',
  'NOT STARTED': 'bg-gray-100 text-gray-700 border border-gray-300',
  COMMITTED: 'bg-purple-100 text-purple-800 border border-purple-300',
  UNKNOWN: 'bg-gray-50 text-gray-500 border border-gray-200',
}

export default function StatusBadge({ status }) {
  const displayText = status?.replace('_', ' ') || 'UNKNOWN'
  
  return (
    <span
      className={clsx(
        'inline-flex items-center',
        'px-3 py-1',
        'rounded-md',
        'text-xs font-medium',
        statusStyles[status] || statusStyles.UNKNOWN
      )}
    >
      {displayText}
    </span>
  )
}
