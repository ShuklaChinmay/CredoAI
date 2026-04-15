import React, { useState } from 'react'

export default function Input({
  label,
  error,
  hint,
  className = '',
  inputClassName = '',
  required,
  type = 'text',
  onEnter,
  ...props
}) {
  const [showPassword, setShowPassword] = useState(false)
  const isPasswordField = type === 'password'
  const inputType = isPasswordField && showPassword ? 'text' : type

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && onEnter && type !== 'textarea') {
      e.preventDefault()
      onEnter()
    }
  }

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label className="text-sm font-medium text-slate-700">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <div className="relative">
        <input
          type={inputType}
          className={[
            'w-full px-3.5 py-2.5 rounded-lg text-sm text-slate-900',
            'bg-white border border-slate-200 outline-none',
            'placeholder:text-slate-400',
            'focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20',
            'transition-all duration-150',
            'disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed',
            isPasswordField ? 'pr-10' : '',
            error ? 'border-red-400 focus:border-red-400 focus:ring-red-400/20' : '',
            inputClassName,
          ].join(' ')}
          onKeyDown={handleKeyDown}
          {...props}
        />
        {isPasswordField && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors text-sm"
            title={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? '👁️' : '👁️‍🗨️'}
          </button>
        )}
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {hint && !error && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  )
}
