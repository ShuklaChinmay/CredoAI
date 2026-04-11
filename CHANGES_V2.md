# LoanAI v2 — Changes from v1

## 3-Agent System (replaces 7 agents)

| Old Agent          | New System                            |
|--------------------|---------------------------------------|
| Master Agent       | Chat Agent (master_agent.py)          |
| Sales Agent        | Loan Agent (loan_agent.py)            |
| Verification Agent | Loan Agent (loan_agent.py)            |
| Underwriting Agent | Loan Agent — eligibility questions    |
| Negotiation Agent  | Removed                               |
| Sanction Agent     | Removed                               |
| Locking Agent      | Removed                               |
| *(new)*            | Document Collector Agent              |

## New Files

### Backend
- `backend/agents/loan_agent.py` — Aryan persona loan advisor
- `backend/agents/document_collector_agent.py` — Collects docs one by one
- `backend/routes/payment.py` — PayPal create-order + capture endpoints

### Frontend
- `src/components/chat/PaymentModal.jsx` — PayPal Smart Buttons modal ($2.49)
- `src/components/chat/FileUploadButton.jsx` — File upload UI

## Modified Files

### Backend
- `backend/agents/master_agent.py` — Rewritten for 3 agents
- `backend/routes/chat.py` — New phase transitions + file upload endpoint
- `backend/main.py` — Added payment router + static file serving
- `backend/models/loan_model.py` — Added LoanApplicationDocument model
- `backend/config/settings.py` — Added PayPal config (PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
- `backend/.env` — Added PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET
- `backend/requirements.txt` — razorpay removed; httpx already present (used for PayPal API calls)

### Frontend
- `frontend/index.html` — PayPal JS SDK script tag
- `src/store/useChatStore.js` — New pipeline steps (4 steps)
- `src/hooks/useAgent.js` — New action/phase mappings
- `src/services/chatService.js` — PayPal create-order + capture calls
- `src/components/chat/ChatWindow.jsx` — PaymentModal + FileUpload
- `src/components/chat/AgentPipeline.jsx` — 4-step progress bar
- `src/components/chat/MessageBubble.jsx` — New agent styles
- `src/components/layout/Topbar.jsx` — Added subtitle prop
- `src/pages/Chat.jsx` — Phase label + payment done badge
- `src/index.css` — New .av-loan, .av-docs, .tag-loan, .tag-docs classes

### Database
- `database/migrations/v2_loan_application_documents.sql` — New table

## PayPal Setup

### 1. Get credentials
Go to: https://developer.paypal.com/dashboard/applications/sandbox  
Create an app → copy Client ID and Secret.

### 2. Add to backend/.env
```
PAYPAL_CLIENT_ID=YOUR_CLIENT_ID
PAYPAL_CLIENT_SECRET=YOUR_CLIENT_SECRET
```

### 3. Update frontend/index.html
Replace `YOUR_PAYPAL_CLIENT_ID` in the SDK script src with your actual Client ID.

### 4. Go live
- Change `PAYPAL_BASE` in `routes/payment.py`:  
  `api-m.sandbox.paypal.com` → `api-m.paypal.com`
- Update SDK URL in `index.html` too.
