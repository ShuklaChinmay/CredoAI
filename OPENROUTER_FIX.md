# OpenRouter Authentication Error - Fix Guide

## Error: `AuthenticationError: Error code: 401 - User not found`

This error occurs when the OpenRouter API key is invalid, expired, or has no active credits.

## Immediate Steps to Fix

### 1. Check Your OpenRouter API Key
- Visit: https://openrouter.ai/account/api_keys
- Verify the API key in your `.env` file matches exactly
- Check for any extra spaces or characters

Current `.env` setting:
```
OPENROUTER_API_KEY=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
```

### 2. Verify Account Status
- Log in to https://openrouter.ai/
- Check if your account has:
  ✓ Active API key (not revoked/deleted)
  ✓ Sufficient credits ($0.01 minimum recommended for testing)
  ✓ No suspension issues

### 3. Generate a New API Key (if needed)
```bash
# If old key is compromised or expired:
1. Go to https://openrouter.ai/account/api_keys
2. Click "Create new key"
3. Copy the new key
4. Update your .env file
5. Restart the server
```

### 4. Test the Connection
```bash
# Test endpoint (added to code)
curl http://localhost:8000/health
```

Expected response if working:
```json
{"status": "ok", "message": "OpenRouter API is working"}
```

If you get an error, it will show the exact problem.

### 5. Restart the Server
```bash
# Stop current server (Ctrl+C in terminal)
# Then restart:
python -m uvicorn chabot.app:app --reload --port 8000
```

## Common Causes & Solutions

| Issue | Solution |
|-------|----------|
| **API Key Invalid** | Generate new key from OpenRouter dashboard |
| **No Credits** | Add payment method or credits to account |
| **Key Expired** | Check expiration date, generate new one if expired |
| **Copy-Paste Error** | Verify no extra spaces in `.env` file |
| **Wrong Base URL** | Ensure `base_url="https://openrouter.ai/api/v1"` (it's correct in code) |

## Testing with Simple Curl

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is your name?",
    "session_id": "test-123"
  }'
```

## Debug Logs

Check the terminal running uvicorn for detailed error messages. The updated code includes better logging to help diagnose issues.

## If Problem Persists

1. Check OpenRouter status page: https://status.openrouter.ai/
2. Try a different model: `openai/gpt-3.5-turbo` (costs more but might work)
3. Check OpenRouter docs: https://openrouter.ai/docs

---

**Last updated:** 2026-04-10
