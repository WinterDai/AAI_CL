import clsx from 'clsx'

export default function Card({ children, className, ...props }) {
  return (
    <div
      className={clsx(
        'bg-white',
        'border border-gray-200',
        'rounded-lg',
        'p-6',
        'hover:shadow-sm',
        'transition-shadow',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
