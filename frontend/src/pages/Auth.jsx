import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import authService from '../services/authService'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { Divider } from '../components/ui/index.jsx'

const AGENTS = ['Loan', 'Document Collector', 'Chat']



export default function Auth() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [mode, setMode] = useState('login')
  const [otpFlow, setOtpFlow] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [pendingEmail, setPendingEmail] = useState('')
  const [pendingOtp, setPendingOtp] = useState('')
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', ''])

  const [form, setForm] = useState({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  useEffect(() => {
    setForm({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
    setError('')
    setOtpDigits(['', '', '', '', '', ''])
  }, [mode])

  useEffect(() => {
    setForm({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
    setError('')
    setOtpDigits(['', '', '', '', '', ''])
  }, [])

  const handleLogin = async () => {
    if (!form.email || !form.password) return setError('Please fill all fields')
    setLoading(true); setError('')

    try {
      const { data } = await authService.login(form.email, form.password)

      console.log("LOGIN RESPONSE:", data)

      setAuth(
        data.user,
        data.access_token || data.token
      )

      navigate('/')

    } catch (e) {
      setError(e.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  // const handleRegister = async () => {
  //   if (!form.name || !form.email || !form.password) return setError('Please fill all fields')
  //   setLoading(true); setError('')
  //   try {
  //     await authService.register({ name: form.name, email: form.email, password: form.password, mobile: form.mobile })
  //     setPendingEmail(form.email)
  //     setOtpFlow('register')
  //     setMode('otp')
  //   } catch (e) {
  //     setError(e.response?.data?.detail || 'Registration failed')
  //   } finally { setLoading(false) }
  // }

  const handleRegister = async () => {
    if (!form.name || !form.email || !form.password) {
      return setError("Please fill all fields");
    }

    setError("");
    setLoading(true);
    
    try {
      const response = await authService.register({
        name: form.name,
        email: form.email,
        password: form.password,
        mobile: form.mobile,
      });

      console.log("✅ Registration successful:", response.data);

      setPendingEmail(form.email);
      setOtpFlow('register');
      
      // Force mode update
      setTimeout(() => {
        setMode('otp');
      }, 100);

    } catch (e) {
      console.error("❌ Registration failed:", e);
      const errorMsg = e.response?.data?.detail || e.message || "Registration failed";
      console.error("Error message:", errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleOTP = async () => {
    const otp = otpDigits.join('')
    if (otp.length < 6) return setError('Enter 6-digit OTP')

    setLoading(true); setError('')

    try {
      // For registration flow
      if (otpFlow === 'register') {
        const { data } = await authService.verifyOtp(pendingEmail, otp)
        setAuth(
          data.user,
          data.access_token || data.token
        )
        navigate('/')
      }
      // For forgot password flow
      else if (otpFlow === 'forgot') {
        setPendingOtp(otp)
        setMode('set_password')
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Invalid OTP')
    } finally {
      setLoading(false)
    }
  }

  const handleForgot = async () => {
    if (!form.email) return setError('Enter your email')
    setLoading(true); setError('')
    try {
      await authService.forgotPassword(form.email)
      setPendingEmail(form.email)
      setOtpFlow('forgot')
      setMode('otp')
    } catch (e) {
      setError(e.response?.data?.detail || 'Error')
    } finally { setLoading(false) }
  }

  const handleResetPassword = async () => {
    if (!form.password || !form.confirmPassword) return setError('Please fill all fields')
    if (form.password !== form.confirmPassword) return setError('Passwords do not match')
    if (form.password.length < 8) return setError('Password must be at least 8 characters')
    
    setLoading(true); setError('')

    try {
      await authService.resetPassword(pendingEmail, pendingOtp, form.password)
      setError('')
      setMode('login')
      setForm({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
      setTimeout(() => {
        setForm({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
      }, 500)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  const otpRef = (i) => (el) => { if (el) el.dataset.idx = i }
  const handleOtpInput = (i, v) => {
    const next = [...otpDigits]
    next[i] = v.slice(-1)
    setOtpDigits(next)
    if (v && i < 5) document.getElementById(`otp-${i + 1}`)?.focus()
  }
  const handleOtpKey = (i, e) => {
    if (e.key === 'Backspace' && !otpDigits[i] && i > 0)
      document.getElementById(`otp-${i - 1}`)?.focus()
  }

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex flex-col justify-between w-[480px] bg-[#0F172A] px-12 py-14 flex-shrink-0">
        <div>
          <div className="font-head text-2xl font-extrabold text-white mb-1">
            Credo<span className="text-blue-400">AI</span>
          </div>
          <div className="text-xs text-white/30 uppercase tracking-widest mb-14">
            Intelligent Loan System
          </div>
          <div className="inline-flex items-center gap-2 bg-blue-500/15 text-blue-400 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
            ✦ Powered by Multi-Agent AI
          </div>
          <h2 className="font-head text-3xl font-extrabold text-white leading-tight mb-4">
            Get Loans the<br /><span className="text-blue-400">Intelligent</span> Way
          </h2>
          <p className="text-sm text-white/50 leading-relaxed mb-8">
            Our AI agent pipeline processes your loan application end-to-end — from KYC to sanction — in minutes, not days.
          </p>
          <div className="flex flex-wrap gap-2">
            {AGENTS.map((a) => (
              <span key={a} className="text-xs bg-white/[0.06] border border-white/[0.08] text-white/60 px-3 py-1.5 rounded-full">
                {a} Agent
              </span>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {[
            { v: '< 5 min', l: 'Approval Time' },
            { v: '3 AI Agents', l: 'In Pipeline' },
            { v: '100%', l: 'Digital Process' },
            { v: '₹2 Cr', l: 'Max Loan' },
          ].map((s) => (
            <div key={s.l} className="bg-white/[0.04] rounded-xl px-4 py-3">
              <div className="font-head text-lg font-bold text-white">{s.v}</div>
              <div className="text-xs text-white/40 mt-0.5">{s.l}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-[380px]">

          {mode === 'otp' && (
            <>
              <h3 className="font-head text-2xl font-bold text-slate-900 mb-1">Verify your email</h3>
              <p className="text-sm text-slate-500 mb-6">
                Enter the 6-digit OTP sent to <strong>{pendingEmail}</strong>
              </p>
              <div className="flex gap-2.5 justify-center mb-6">
                {otpDigits.map((d, i) => (
                  <input
                    key={i}
                    id={`otp-${i}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={d}
                    onChange={(e) => handleOtpInput(i, e.target.value)}
                    onKeyDown={(e) => handleOtpKey(i, e)}
                    className="w-11 h-13 text-center text-xl font-bold border-2 border-slate-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
                  />
                ))}
              </div>
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <Button variant="navy" fullWidth loading={loading} onClick={handleOTP} className="mb-3">
                Verify OTP
              </Button>
              <button onClick={() => otpFlow === 'register' ? setMode('register') : setMode('forgot')} className="text-sm text-slate-500 hover:text-blue-600 transition-colors w-full text-center">
                ← Back
              </button>
            </>
          )}

          {mode === 'set_password' && (
            <>
              <h3 className="font-head text-2xl font-bold text-slate-900 mb-1">Set new password</h3>
              <p className="text-sm text-slate-500 mb-6">Create a strong password for your account</p>
              <div className="space-y-4 mb-5">
                <Input 
                  label="New Password" 
                  type="password" 
                  placeholder="Min 8 characters" 
                  value={form.password} 
                  onChange={set('password')} 
                  required 
                  autoComplete="new-password" 
                />
                <Input 
                  label="Confirm Password" 
                  type="password" 
                  placeholder="Confirm your password" 
                  value={form.confirmPassword} 
                  onChange={set('confirmPassword')} 
                  required 
                  autoComplete="new-password" 
                />
              </div>
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <Button variant="navy" fullWidth loading={loading} onClick={handleResetPassword} className="mb-3">
                Reset Password
              </Button>
              <button onClick={() => setMode('login')} className="text-sm text-slate-500 hover:text-blue-600 w-full text-center">
                ← Back to login
              </button>
            </>
          )}

          {mode === 'forgot' && (
            <>
              <h3 className="font-head text-2xl font-bold text-slate-900 mb-1">Reset password</h3>
              <p className="text-sm text-slate-500 mb-6">Enter your email to receive a reset OTP</p>
              <Input label="Email" type="email" placeholder="your@example.com" value={form.email} onChange={set('email')} className="mb-4" autoComplete="username" />
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <Button variant="navy" fullWidth loading={loading} onClick={handleForgot} className="mb-3">Send OTP</Button>
              <button onClick={() => setMode('login')} className="text-sm text-slate-500 hover:text-blue-600 w-full text-center">← Back to login</button>
            </>
          )}

          {mode === 'login' && (
            <>
              <h3 className="font-head text-2xl font-bold text-slate-900 mb-1">Welcome back</h3>
              <p className="text-sm text-slate-500 mb-6">Sign in to continue to CredoAI</p>
              <div className="space-y-4 mb-2">
                <Input label="Email" type="email" placeholder="your@example.com" value={form.email} onChange={set('email')} required autoComplete="off" />
                <Input label="Password" type="password" placeholder="••••••••" value={form.password} onChange={set('password')} required autoComplete="off" />
              </div>
              <div className="text-right mb-4">
                <button onClick={() => setMode('forgot')} className="text-xs text-blue-600 hover:underline">
                  Forgot password?
                </button>
              </div>
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <Button variant="navy" fullWidth loading={loading} onClick={handleLogin} className="mb-3">
                Sign In
              </Button>
              <Divider label="or" />
              <p className="text-sm text-center text-slate-500">
                No account?{' '}
                <button onClick={() => setMode('register')} className="text-blue-600 font-medium hover:underline">
                  Register
                </button>
              </p>
            </>
          )}

          {mode === 'register' && (
            <>
              <h3 className="font-head text-2xl font-bold text-slate-900 mb-1">Create account</h3>
              <p className="text-sm text-slate-500 mb-6">Start your loan journey today</p>
              <div className="space-y-4 mb-5">
                <Input label="Full Name" placeholder="Your Name" value={form.name} onChange={set('name')} required autoComplete="name" />
                <Input label="Email" type="email" placeholder="your@example.com" value={form.email} onChange={set('email')} required autoComplete="username" />
                <Input label="Password" type="password" placeholder="Min 8 characters" value={form.password} onChange={set('password')} required autoComplete="new-password" />
                <Input label="Mobile (optional)" placeholder="+91 98765 43210" value={form.mobile} onChange={set('mobile')} autoComplete="tel" />
              </div>
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <Button variant="navy" fullWidth loading={loading} onClick={handleRegister} className="mb-4">
                Create Account
              </Button>
              <p className="text-sm text-center text-slate-500">
                Already registered?{' '}
                <button onClick={() => setMode('login')} className="text-blue-600 font-medium hover:underline">
                  Sign In
                </button>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
