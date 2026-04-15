import React from 'react'

const variants = {
  primary:  'bg-blue-600 hover:bg-blue-700 text-white border-transparent',
  secondary:'bg-white hover:bg-slate-50 text-slate-700 border-slate-200',
  ghost:    'bg-transparent hover:bg-slate-100 text-slate-600 border-transparent',
  danger:   'bg-red-600 hover:bg-red-700 text-white border-transparent',
  success:  'bg-green-600 hover:bg-green-700 text-white border-transparent',
  navy:     'bg-[#0F172A] hover:bg-[#1E293B] text-white border-transparent',
}

const sizes = {
  xs: 'px-2.5 py-1 text-xs gap-1',
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2 text-sm gap-2',
  lg: 'px-5 py-2.5 text-base gap-2',
}

export default function Button({
  children,
  variant = 'secondary',
  size = 'md',
  className = '',
  loading = false,
  icon,
  fullWidth = false,
  ...props
}) {
  return (
    <button
      className={[
        'inline-flex items-center justify-center font-medium rounded-lg border',
        'transition-all duration-150 active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        fullWidth ? 'w-full' : '',
        className,
      ].join(' ')}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : icon ? (
        <span className="text-base leading-none">{icon}</span>
      ) : null}
      {children}
    </button>
    )
}
