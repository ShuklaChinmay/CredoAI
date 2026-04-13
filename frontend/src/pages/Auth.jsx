import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import authService from '../services/authService'
import api from '../services/api'
import emailService from '../services/emailService'
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
  const [pendingUserId, setPendingUserId] = useState('')
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', ''])
  const [resendCountdown, setResendCountdown] = useState(0)
  const [otpExpireCountdown, setOtpExpireCountdown] = useState(0)

  const [form, setForm] = useState({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  // Define handleOtpTimeout FIRST before any useEffect uses it
  const handleOtpTimeout = useCallback(async () => {
    console.log("⏰ handleOtpTimeout CALLED")
    console.log("Pending User ID:", pendingUserId)
    
    if (!pendingUserId) {
      console.error("❌ No pendingUserId available for deletion")
      setError('OTP expired. Please register again.')
      setMode('register')
      return
    }

    try {
      console.log(`🗑️ Calling DELETE endpoint for user: ${pendingUserId}`)
      const response = await api.delete(`/auth/cancel-registration/${pendingUserId}`)
      console.log("✅ Delete response:", response.data)
    } catch (err) {
      console.error("❌ Error calling delete endpoint:", err)
      if (err.response?.data?.detail) {
        console.error("Backend error:", err.response.data.detail)
      }
    }
    
    setError('⏱️ Registration OTP expired. Your data has been removed. Please register again.')
    setOtpExpireCountdown(0)
    setPendingUserId('')
    setPendingEmail('')
    setOtpDigits(['', '', '', '', '', ''])
    
    setTimeout(() => {
      setMode('register')
      setForm({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
    }, 2000)
  }, [pendingUserId])

  useEffect(() => {
    // Only reset state when NOT entering OTP mode
    // OTP timers are managed by their respective handlers
    if (mode !== 'otp') {
      setForm({ name: '', email: '', password: '', mobile: '', confirmPassword: '' })
      setError('')
      setOtpDigits(['', '', '', '', '', ''])
      setResendCountdown(0)
      setOtpExpireCountdown(0)
    }
  }, [mode])

  // Resend OTP cooldown timer (2 minutes)
  useEffect(() => {
    if (resendCountdown <= 0) return
    const timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000)
    return () => clearTimeout(timer)
  }, [resendCountdown])

  // OTP expiration timer (10 minutes) - only for registration
  useEffect(() => {
    if (otpExpireCountdown <= 0 || otpFlow !== 'register') return
    
    console.log(`⏰ Timer running: ${otpExpireCountdown}s remaining, User ID: ${pendingUserId}`)
    
    const timer = setTimeout(() => setOtpExpireCountdown(otpExpireCountdown - 1), 1000)
    
    return () => clearTimeout(timer)
  }, [otpExpireCountdown, otpFlow])

  // Trigger timeout handler when countdown reaches 0
  useEffect(() => {
    if (otpExpireCountdown === 0 || otpFlow !== 'register') return
    
    if (otpExpireCountdown <= 1) {
      console.log("⏰ TIMEOUT TRIGGERED - About to delete user")
      handleOtpTimeout()
    }
  }, [otpExpireCountdown, otpFlow, handleOtpTimeout])

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

      const { email, otp, user_id } = response.data;
      
      console.log("📌 Extracted from response:")
      console.log("  - email:", email)
      console.log("  - otp:", otp)
      console.log("  - user_id:", user_id)

      if (!user_id) {
        console.error("❌ CRITICAL: user_id is missing from registration response!")
        setError("Registration error: User ID not received. Please try again.")
        setLoading(false)
        return
      }

      // Send OTP email via frontend using registration template
      setLoading(true);
      const emailResult = await emailService.sendRegistrationOTP(email, otp, form.name);
      
      if (emailResult.success) {
        console.log("✅ OTP email sent successfully");
        console.log("🚀 Setting pendingUserId to:", user_id)
        setPendingEmail(email);
        setPendingUserId(user_id);
        setOtpFlow('register');
        setOtpDigits(['', '', '', '', '', '']); // Keep empty - user must enter manually
        setResendCountdown(120); // 2 minute resend timer
        setOtpExpireCountdown(600); // 10 minutes in seconds
        setMode('otp');
      } else {
        // Delete user if email fails
        setError(`OTP generated but email failed: ${emailResult.message}`);
        try {
          console.log(`🗑️ Email failed, deleting user ${user_id}`)
          const deleteResponse = await api.delete(`/auth/cancel-registration/${user_id}`)
          console.log("✅ User deleted after email failure:", deleteResponse.data)
        } catch (err) {
          console.error("❌ Error deleting user after email failure:", err)
        }
      }

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
        setOtpExpireCountdown(0) // Stop timer on success
        navigate('/')
      }
      // For forgot password flow
      else if (otpFlow === 'forgot') {
        setPendingOtp(otp)
        setMode('set_password')
      }
    } catch (e) {
      const errorDetail = e.response?.data?.detail || 'Invalid OTP'
      if (errorDetail.includes('Invalid OTP') || errorDetail.includes('otp')) {
        setError('❌ Incorrect OTP. Please try again.')
      } else {
        setError(errorDetail)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleForgot = async () => {
    if (!form.email) return setError('Enter your email')
    setLoading(true); setError('')
    try {
      const response = await authService.forgotPassword(form.email)
      const { email, otp, user_found } = response.data
      
      if (!user_found) {
        setError('❌ User not found. Please check your email or register first.')
        setLoading(false)
        return
      }
      
      // Send OTP email via frontend using forgot password template
      const emailResult = await emailService.sendForgotPasswordOTP(email, otp, 'User')
      
      if (emailResult.success) {
        console.log("✅ Forgot password OTP email sent")
        setPendingEmail(email)
        setOtpFlow('forgot')
        setOtpDigits(['', '', '', '', '', '']) // Keep empty - user must enter manually
        setResendCountdown(120) // 2 minutes resend timer
        setMode('otp')
      } else {
        setError(`OTP generated but email failed: ${emailResult.message}`)
      }
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

  const handleResendOTP = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await authService.resendOtp(pendingEmail)
      const { otp } = response.data
      
      // Send OTP email via frontend using correct template based on flow
      const emailResult = otpFlow === 'forgot' 
        ? await emailService.sendForgotPasswordOTP(pendingEmail, otp, 'User')
        : await emailService.sendRegistrationOTP(pendingEmail, otp, 'User')
      
      if (emailResult.success) {
        console.log("✅ Resent OTP email successfully")
        // DO NOT auto-fill OTP - user must enter it manually
        // setOtpDigits(otp.split(""))
        setOtpDigits(['', '', '', '', '', '']) // Clear OTP fields instead
        setResendCountdown(120) // 2 minutes countdown
        setError('OTP sent! Check your email and enter it manually.') 
      } else {
        setError(`OTP regenerated but email failed: ${emailResult.message}`)
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to resend OTP')
    } finally {
      setLoading(false)
    }
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
              <p className="text-sm text-slate-500 mb-2">
                Enter the 6-digit OTP sent to <strong>{pendingEmail}</strong>
              </p>
              <p className="text-sm text-red-600 mb-2 font-semibold">
                Note: Check your mail Inbox and Spam
              </p>
              {otpFlow === 'register' && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-red-700 font-bold text-center">
                    ⏱️ Auto-Delete Timer: {Math.floor(otpExpireCountdown / 60)}:{String(otpExpireCountdown % 60).padStart(2, '0')}
                  </p>
                  <p className="text-xs text-red-600 text-center mt-1">
                    (Registration data will be deleted if OTP is not verified)
                  </p>
                </div>
              )}
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
              <Button variant="navy" fullWidth loading={loading} onClick={handleOTP} className="mb-4">
                Verify OTP
              </Button>
              
              {/* Resend OTP Button with Timer - Blue when disabled, Navy when enabled */}
              {resendCountdown > 0 ? (
                <Button 
                  variant="primary" 
                  fullWidth 
                  disabled={true}
                  onClick={handleResendOTP}
                  className="mb-4"
                >
                  ⏱️ Resend OTP in {Math.floor(resendCountdown / 60)}:{String(resendCountdown % 60).padStart(2, '0')}
                </Button>
              ) : (
                <Button 
                  variant="navy" 
                  fullWidth 
                  loading={loading}
                  onClick={handleResendOTP}
                  className="mb-4"
                >
                  🔄 Resend OTP
                </Button>
              )}
              
              <button onClick={() => otpFlow === 'register' ? setMode('register') : setMode('forgot')} className="text-sm text-slate-500 hover:text-blue-600 transition-colors w-full text-center mb-4">
                ← Back
              </button>
              <div className="border-t border-slate-100 pt-4">
                <p className="text-xs text-slate-500 text-center">
                  Didn't receive OTP? Email{' '}
                  <a href="mailto:credoai.org@gmail.com" className="text-blue-600 font-medium hover:underline">
                    credoai.org@gmail.com
                  </a>
                </p>
              </div>
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
              <button onClick={() => setMode('login')} className="text-sm text-slate-500 hover:text-blue-600 w-full text-center mb-4">
                ← Back to login
              </button>
              <div className="border-t border-slate-100 pt-4">
                <p className="text-xs text-slate-500 text-center">
                  Need assistance? Contact us at{' '}
                  <a href="mailto:credoai.org@gmail.com" className="text-blue-600 font-medium hover:underline">
                    credoai.org@gmail.com
                  </a>
                </p>
              </div>
            </>
          )}

          {mode === 'forgot' && (
            <>
              <h3 className="font-head text-2xl font-bold text-slate-900 mb-1">Reset password</h3>
              <p className="text-sm text-slate-500 mb-6">Enter your email to receive a reset OTP</p>
              <Input label="Email" type="email" placeholder="your@example.com" value={form.email} onChange={set('email')} className="mb-4" autoComplete="username" />
              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
              <Button variant="navy" fullWidth loading={loading} onClick={handleForgot} className="mb-3">Send OTP</Button>
              <button onClick={() => setMode('login')} className="text-sm text-slate-500 hover:text-blue-600 w-full text-center mb-4">← Back to login</button>
              <div className="border-t border-slate-100 pt-4">
                <p className="text-xs text-slate-500 text-center">
                  Need help? Contact our support team at{' '}
                  <a href="mailto:credoai.org@gmail.com" className="text-blue-600 font-medium hover:underline">
                    credoai.org@gmail.com
                  </a>
                </p>
              </div>
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
              <div className="border-t border-slate-100 mt-4 pt-4">
                <p className="text-xs text-slate-500 text-center">
                  Having trouble? Contact support at{' '}
                  <a href="mailto:credoai.org@gmail.com" className="text-blue-600 font-medium hover:underline">
                    credoai.org@gmail.com
                  </a>
                </p>
              </div>
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
              <div className="border-t border-slate-100 mt-4 pt-4">
                <p className="text-xs text-slate-500 text-center">
                  Questions? Reach out to us at{' '}
                  <a href="mailto:credoai.org@gmail.com" className="text-blue-600 font-medium hover:underline">
                    credoai.org@gmail.com
                  </a>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
