import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout'
import Topbar from '../components/layout/Topbar'
import Button from '../components/ui/Button'
import { Card } from '../components/ui/index.jsx'
import loanService, { formatINR } from '../services/loanService'
import useLoanStore from '../store/useLoanStore'
import useAuthStore from '../store/useAuthStore'

const FALLBACK_LOANS = [
  {
    id: 1, icon: '👤', name: 'Personal Loan', loan_type: 'personal', product_code: 'PL-STD',
    min_rate: 10.5, max_amount: 2500000, min_tenure_months: 12, max_tenure_months: 60,
    eligibility_notes: '₹25,000+ monthly income', is_active: true,
    description: 'Unsecured personal loan for any legitimate purpose. No collateral required.',
    features: ['No collateral required','Minimal documentation','Quick disbursal'],
    documents_needed: ['Aadhaar Card','PAN Card','Salary slips','Bank statement'],
  },
  {
    id: 2, icon: '🏠', name: 'Home Loan', loan_type: 'home', product_code: 'HL-STD',
    min_rate: 8.4, max_amount: 20000000, min_tenure_months: 60, max_tenure_months: 360,
    eligibility_notes: '₹40,000+ monthly income', is_active: true,
    description: 'Purchase or construct your dream home with lowest interest rates.',
    features: ['Tax benefits u/s 24','Balance transfer','Top-up facility'],
    documents_needed: ['Aadhaar & PAN','Property documents','ITR (2 years)'],
  },
  {
    id: 3, icon: '🚗', name: 'Car Loan', loan_type: 'car', product_code: 'CAR-NEW',
    min_rate: 9.25, max_amount: 5000000, min_tenure_months: 12, max_tenure_months: 84,
    eligibility_notes: '₹30,000+ monthly income', is_active: true,
    description: 'Drive your dream car with up to 100% on-road funding.',
    features: ['Up to 100% on-road funding','New & used vehicles','Foreclosure allowed'],
    documents_needed: ['Aadhaar & PAN','Driving license','Salary slips'],
  },
  {
    id: 4, icon: '🎓', name: 'Education Loan', loan_type: 'education', product_code: 'EDU-STD',
    min_rate: 7.8, max_amount: 4000000, min_tenure_months: 12, max_tenure_months: 180,
    eligibility_notes: 'Valid admission letter', is_active: true,
    description: 'Fund higher education in India or abroad with moratorium period.',
    features: ['Covers tuition + living','Tax benefit u/s 80E','Moratorium period'],
    documents_needed: ['Admission letter','Fee structure','Aadhaar & PAN'],
  },
  {
    id: 5, icon: '💼', name: 'Business Loan', loan_type: 'business', product_code: 'BIZ-MSME',
    min_rate: 12.0, max_amount: 7500000, min_tenure_months: 12, max_tenure_months: 72,
    eligibility_notes: '2+ years business vintage', is_active: true,
    description: 'Fuel business growth with working capital or expansion funds.',
    features: ['No collateral for MSME','Overdraft facility','GST-based eligibility'],
    documents_needed: ['GST returns','Business registration','ITR (2 years)'],
  },
  {
    id: 6, icon: '💰', name: 'Gold Loan', loan_type: 'gold', product_code: 'GOLD-STD',
    min_rate: 7.5, max_amount: 3000000, min_tenure_months: 3, max_tenure_months: 36,
    eligibility_notes: 'Gold jewellery as collateral', is_active: true,
    description: 'Instant liquidity against gold jewellery at 75% LTV.',
    features: ['Instant disbursal','Up to 75% LTV','Free gold storage'],
    documents_needed: ['Aadhaar & PAN','Gold jewellery','Address proof'],
  },
]

function formatMax(n) {
  if (!n) return '—'
  if (n >= 10_000_000) return `₹${(n / 10_000_000).toFixed(0)} Cr`
  if (n >= 100_000)    return `₹${(n / 100_000).toFixed(0)} L`
  return formatINR(n)
}

export default function Explore() {
  const navigate  = useNavigate()
  const { addApplication } = useLoanStore()
  const [loans, setLoans]     = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [applying, setApplying] = useState(null)
  const [toast, setToast] = useState(null)

  const handleApply = async (loan) => {
    setApplying(loan.id)
    try {
      const { data } = await loanService.applyLoan({
        loan_type: loan.loan_type,
        requested_amount: loan.max_amount,
        purpose: `Applied from Explore page for ${loan.name}`,
      })
      
      const backendLoanId = data.loan_id
      
      const newApp = {
        id: backendLoanId,
        loan_id: backendLoanId,
        _id: backendLoanId,
        name: loan.name,
        loan_type: loan.loan_type,
        icon: loan.icon,
        status: 'pending',
        requested_amount: loan.max_amount,
        created_at: new Date().toISOString(),
        documents: [],
        product_code: loan.product_code,
      }
      
      addApplication(newApp)
      
      setToast({ msg: `✓ ${loan.name} added to your applications`, type: 'success' })
      setTimeout(() => setToast(null), 2000)
      
      setTimeout(() => {
        navigate('/dashboard')
      }, 500)
    } catch (e) {
      setToast({ msg: '❌ Failed to apply. Please try again.', type: 'error' })
      setTimeout(() => setToast(null), 3000)
    } finally {
      setApplying(null)
    }
  }

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const { data } = await loanService.getActiveProducts()
        setLoans(data.products?.length ? data.products : FALLBACK_LOANS)
      } catch (_) {
        setLoans(FALLBACK_LOANS)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <AppLayout>
      <Topbar title="Explore Loans" />
      {toast && (
        <div className={['fixed top-4 right-4 z-50 px-5 py-3 rounded-xl shadow-lg text-sm font-medium animate-slide-in',
          toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-green-600 text-white'].join(' ')}>
          {toast.msg}
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-6">

        <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-3.5 mb-6 flex items-center justify-between flex-wrap gap-3">
          <div>
            <p className="text-sm font-semibold text-blue-800">Find the right loan for you</p>
            <p className="text-xs text-blue-600 mt-0.5">
              Compare rates and features · {loans.length} products available
            </p>
          </div>
          <Button variant="primary" size="sm" onClick={() => navigate('/chat')}>
            💬 Apply via AI Agent →
          </Button>
        </div>

        {loading && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {[1,2,3,4].map((n) => (
              <div key={n} className="bg-white rounded-xl border border-slate-100 p-5 animate-pulse">
                <div className="flex gap-4 mb-4">
                  <div className="w-12 h-12 bg-slate-100 rounded-xl" />
                  <div className="flex-1 space-y-2 pt-1">
                    <div className="h-4 bg-slate-100 rounded w-2/3" />
                    <div className="h-3 bg-slate-100 rounded w-1/3" />
                  </div>
                </div>
                <div className="h-3 bg-slate-100 rounded mb-2" />
                <div className="h-3 bg-slate-100 rounded w-4/5 mb-4" />
                <div className="grid grid-cols-3 gap-2">
                  {[1,2,3].map((i) => <div key={i} className="h-12 bg-slate-100 rounded-lg" />)}
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && loans.length === 0 && (
          <div className="text-center py-20 text-slate-400">
            <div className="text-5xl mb-3">📦</div>
            <p className="font-semibold text-slate-600 mb-1">No loan products available</p>
            <p className="text-sm">Ask an admin to add loan schemes via the Admin Panel.</p>
          </div>
        )}

        {!loading && loans.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {loans.map((loan, index) => {
              // Use a unique identifier: prefer id, then product_code, then index
              const loanId = loan.id || loan.product_id || loan.product_code || `loan-${index}`
              const isOpen = expanded === loanId
              const tenure = `${loan.min_tenure_months}–${loan.max_tenure_months} mo`
              console.log(`[${index}] Loan: ${loan.name} | loanId: ${loanId} | expanded: ${expanded} | isOpen: ${isOpen}`)
              return (
                <Card key={loanId} className="p-0 overflow-hidden">
                  {/* Main content */}
                  <div className="p-5">
                    <div className="flex items-start gap-4 mb-3">
                      <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-2xl flex-shrink-0">
                        {loan.icon || '💰'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <h3 className="font-head text-base font-bold text-slate-900">{loan.name}</h3>
                        </div>
                        <p className="text-xs text-slate-500">{loan.eligibility_notes}</p>
                      </div>
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed mb-4">{loan.description}</p>
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { label: 'Provider', value: loan.loan_provider_bank || 'N/A' },
                        { label: 'Amount', value: `${formatMax(loan.min_amount)} – ${formatMax(loan.max_amount)}` },
                        { label: 'Interest', value: `${loan.interest_rate || loan.min_rate || '—'}%` },
                        { label: 'Tenure', value: `${loan.min_tenure_months}–${loan.max_tenure_months}mo` },
                      ].map((f) => (
                        <div key={f.label} className="bg-slate-50 rounded-lg px-3 py-2.5">
                          <p className="text-[9px] text-slate-400 uppercase tracking-wide mb-0.5 font-semibold">{f.label}</p>
                          <p className="text-sm font-bold text-slate-700">
                            {f.value}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      console.log(`Button clicked! Current expanded: ${expanded}, loanId: ${loanId}, will set to: ${isOpen ? 'null' : loanId}`)
                      setExpanded(isOpen ? null : loanId)
                    }}
                    className="w-full px-5 py-2.5 bg-slate-50 border-t border-slate-100 text-xs font-medium text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition-colors flex items-center justify-center gap-1.5"
                  >
                    {isOpen ? '▲ Show less' : '▾ View Features & Documents'}
                  </button>

                  {isOpen && (
                    <div className="px-5 pb-5 pt-4 border-t border-slate-100 space-y-4">
                      {/* Loan Conditions */}
                      {loan.loan_conditions?.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Loan Conditions</p>
                          <ul className="space-y-1.5">
                            {loan.loan_conditions.map((cond, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                                <span className="text-amber-500 text-xs flex-shrink-0 mt-0.5">•</span> {cond}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      <div className="grid grid-cols-2 gap-5">
                        {loan.features?.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Key Features</p>
                            <ul className="space-y-1.5">
                              {loan.features.map((f, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                                  <span className="w-4 h-4 rounded-full bg-green-100 text-green-600 text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">✓</span>
                                  {f}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {loan.documents_needed?.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Documents Needed</p>
                            <ul className="space-y-1.5">
                              {loan.documents_needed.map((d, i) => (
                                <li key={i} className="flex items-center gap-2 text-sm text-slate-600">
                                  <span className="text-slate-400 text-xs">📄</span> {d}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="bg-slate-50 rounded-lg p-2">
                          <p className="text-slate-400 mb-0.5">Processing Fee</p>
                          <p className="font-bold text-slate-700">{loan.processing_fee_pct ?? 1}% of loan amount</p>
                        </div>
                        <div className="bg-slate-50 rounded-lg p-2 relative group cursor-help">
                          <div className="flex items-center gap-1 mb-0.5">
                            <p className="text-slate-400">Residual Income</p>
                            <div className="w-4 h-4 rounded-full bg-blue-100 text-blue-600 text-[10px] font-bold flex items-center justify-center flex-shrink-0">i</div>
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-44 bg-slate-900 text-white text-xs rounded-lg p-2.5 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10 whitespace-normal">
                              Residual Income is the final income left after paying all ongoing EMIs and insurance premiums.
                              <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-900 transform rotate-45"></div>
                            </div>
                          </div>
                          <p className="font-bold text-slate-700">
                            {loan.residual_income > 0 ? formatINR(loan.residual_income) : 'No minimum'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex gap-3">
                        <Button 
                          variant="primary" 
                          fullWidth 
                          onClick={(e) => {
                            e.stopPropagation()
                            handleApply(loan)
                          }}
                          disabled={applying === loan.id}
                        >
                          {applying === loan.id ? '⏳ Applying...' : `✓ Apply for ${loan.name}`}
                        </Button>
                        <Button 
                          variant="secondary" 
                          fullWidth 
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate('/chat', { state: { selectedLoan: loan } })
                          }}
                        >
                          💬 Ask AI →
                        </Button>
                      </div>
                    </div>
                  )}
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
