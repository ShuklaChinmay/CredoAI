import React, { useState, useEffect, useRef } from 'react'
import useChatStore from '../../store/useChatStore'
import chatService from '../../services/chatService'

function UpiQR({ upiDeeplink, size = 180 }) {
  const encoded = encodeURIComponent(upiDeeplink)
  const src = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encoded}`
  return (
    <img
      src={src}
      alt="UPI QR Code"
      width={size}
      height={size}
      className="rounded-xl border border-slate-100 shadow-sm"
      onError={(e) => { e.target.style.display = 'none' }}
    />
  )
}

export default function PaymentModal({ onPaymentSuccess }) {
  const {
    loanApplicationId, showPaymentModal,
    setShowPaymentModal, setPaymentComplete, setPhase,
  } = useChatStore()

  const [step, setStep]         = useState('loading')
  const [order, setOrder]       = useState(null)
  const [utr, setUtr]           = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errMsg, setErrMsg]     = useState('')
  const [copied, setCopied]     = useState(false)
  const hasFetched              = useRef(false)

  useEffect(() => {
    if (!showPaymentModal || hasFetched.current) return
    hasFetched.current = true
    ;(async () => {
      try {
        const res = await chatService.createPaymentOrder(loanApplicationId)
        setOrder(res.data)
        setStep('pay')
      } catch (e) {
        setErrMsg(e?.response?.data?.detail || 'Could not create payment order. Please try again.')
        setStep('error')
      }
    })()
  }, [showPaymentModal, loanApplicationId])

  const handleClose = () => {
    setShowPaymentModal(false)
    hasFetched.current = false
    setStep('loading')
    setOrder(null)
    setUtr('')
    setErrMsg('')
  }

  const copyUpiId = () => {
    navigator.clipboard?.writeText(order?.upi_id || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const openUpiApp = () => {
    if (order?.upi_deeplink) window.location.href = order.upi_deeplink
  }

  const handleConfirmPayment = async () => {
    if (!utr.trim() || utr.trim().length < 6) {
      setErrMsg('Please enter a valid UTR / transaction ID (min 6 characters)')
      return
    }
    setSubmitting(true)
    setErrMsg('')
    try {
      await chatService.verifyPayment({
        loan_application_id: loanApplicationId,
        utr: utr.trim(),
        payment_method: 'upi',
      })
      setStep('success')
      setPaymentComplete(true)
      setPhase('completed')
      setTimeout(() => {
        handleClose()
        onPaymentSuccess?.()
      }, 2200)
    } catch (e) {
      setErrMsg(e?.response?.data?.detail || 'Verification failed. Check your UTR and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!showPaymentModal) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden animate-fade-up">

        <div className="bg-gradient-to-r from-violet-600 to-indigo-700 px-5 py-4 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center text-lg">💳</div>
            <div>
              <p className="font-head font-bold text-sm">Document Processing Fee</p>
              <p className="text-violet-200 text-xs">Pay via UPI · ₹199 only</p>
            </div>
          </div>
          <button onClick={handleClose} className="text-white/60 hover:text-white text-xl leading-none">×</button>
        </div>

        <div className="p-5">

          {step === 'loading' && (
            <div className="flex flex-col items-center py-8 gap-3">
              <svg className="animate-spin w-8 h-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              <p className="text-sm text-slate-500">Setting up payment...</p>
            </div>
          )}

          {step === 'error' && (
            <div className="py-6 text-center">
              <div className="text-3xl mb-3">❌</div>
              <p className="text-sm text-red-600 mb-4">{errMsg}</p>
              <button
                onClick={() => { setStep('loading'); hasFetched.current = false }}
                className="text-sm text-indigo-600 underline"
              >Retry</button>
            </div>
          )}

          {step === 'success' && (
            <div className="py-6 text-center">
              <div className="text-4xl mb-3">🎉</div>
              <p className="font-head font-bold text-slate-900 text-base mb-1">Payment Confirmed!</p>
              <p className="text-sm text-slate-500">Your application has been submitted.</p>
            </div>
          )}

          {step === 'pay' && order && (
            <>
              <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-center mb-4">
                <p className="text-xs text-slate-500 mb-0.5">Amount to Pay</p>
                <p className="font-head text-3xl font-bold text-indigo-700">₹{order.amount}</p>
              </div>

              <div className="flex gap-4 mb-4">
                <div className="flex-shrink-0">
                  <UpiQR upiDeeplink={order.upi_deeplink} size={130} />
                </div>
                <div className="flex flex-col justify-center gap-2.5 text-xs text-slate-600">
                  <p className="font-semibold text-slate-800 text-sm">Scan QR to pay</p>
                  <p>Open any UPI app:<br/>
                    <span className="font-medium">GPay · PhonePe · Paytm · BHIM</span>
                  </p>
                  <p className="text-slate-400">or click the button below</p>
                </div>
              </div>

              <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 mb-3">
                <span className="text-xs text-slate-500 flex-1">UPI ID: <strong className="text-slate-800">{order.upi_id}</strong></span>
                <button
                  onClick={copyUpiId}
                  className="text-xs text-indigo-600 font-medium hover:text-indigo-800 flex-shrink-0"
                >
                  {copied ? '✓ Copied' : 'Copy'}
                </button>
              </div>

              <button
                onClick={openUpiApp}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold py-2.5 rounded-xl mb-3 transition-colors"
              >
                📱 Open UPI App
              </button>

              <button
                onClick={() => setStep('confirm')}
                className="w-full border border-indigo-200 text-indigo-600 text-sm font-medium py-2.5 rounded-xl hover:bg-indigo-50 transition-colors"
              >
                I've paid — Enter Transaction ID →
              </button>
            </>
          )}

          {step === 'confirm' && (
            <>
              <p className="text-sm font-semibold text-slate-800 mb-1">Confirm your payment</p>
              <p className="text-xs text-slate-400 mb-4">
                Enter the UPI Transaction ID / UTR number from your payment app to confirm.
              </p>

              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                UPI Transaction ID / UTR
              </label>
              <input
                type="text"
                value={utr}
                onChange={(e) => setUtr(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !submitting && utr.trim()) {
                    e.preventDefault()
                    handleConfirmPayment()
                  }
                }}
                placeholder="e.g. 412345678901"
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 mb-3"
                autoFocus
              />

              {errMsg && (
                <p className="text-xs text-red-500 mb-3">{errMsg}</p>
              )}

              <button
                onClick={handleConfirmPayment}
                disabled={submitting || !utr.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-xl mb-2 transition-colors flex items-center justify-center gap-2"
              >
                {submitting
                  ? <><svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Verifying...</>
                  : '✓ Confirm Payment'
                }
              </button>

              <button
                onClick={() => { setStep('pay'); setErrMsg('') }}
                className="w-full text-slate-400 hover:text-slate-600 text-xs py-1.5 transition-colors"
              >
                ← Back to QR
              </button>
            </>
          )}

          {(step === 'pay' || step === 'confirm') && (
            <p className="text-center text-[10px] text-slate-400 mt-3 flex items-center justify-center gap-1">
              🔒 Secure · Ref: {order?.order_id}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
