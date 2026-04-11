from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional, Any
from dotenv import load_dotenv
import os
import re
import requests

load_dotenv(dotenv_path=".env")

app = FastAPI()

def fetch_loan_products():
    try:
        res = requests.get("http://127.0.0.1:8000/loan/products")
        return res.json().get("products", [])
    except Exception as e:
        print("Loan Fetch Error:", e)
        return []

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    selected_loan: Optional[Any] = None
    username: Optional[str] = None


sessions = {}


def extract_income(text):
    match = re.search(r"(income\s*is\s*|salary\s*is\s*)(\d+)", text.lower())
    return int(match.group(2)) if match else None

def format_indian_currency(amount):
    """Format amount in Indian currency style (e.g., 1000000 -> 10L or ₹10,00,000)"""
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return "N/A"
    
    if amount >= 10000000:  # >= 1 Crore
        crores = amount / 10000000
        if crores == int(crores):
            return f"₹{int(crores)}Cr"
        return f"₹{crores:.1f}Cr"
    elif amount >= 100000:  # >= 1 Lakh
        lakhs = amount / 100000
        if lakhs == int(lakhs):
            return f"₹{int(lakhs)}L"
        return f"₹{lakhs:.1f}L"
    else:
        return f"₹{amount:,}"


@app.post("/chat")
def chat(req: ChatRequest):

    session_id = req.session_id
    selected_loan = req.selected_loan
    username = req.username or "friend"
    loan_products = fetch_loan_products()

    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "user_data": {"name": username},
            "selected_loan": selected_loan,
            "step": "loan_explanation" if selected_loan else "name"
        }
        
        
        if selected_loan:
            features_str = ", ".join(selected_loan.get('features', ['N/A'])[:3]) if selected_loan.get('features') else 'N/A'
            desc = selected_loan.get('description', 'A great loan product')
            all_features = ", ".join(selected_loan.get('features', [])) if selected_loan.get('features') else 'N/A'
            documents_str = ", ".join(selected_loan.get('documents_needed', [])) if selected_loan.get('documents_needed') else 'N/A'
            
            greeting = f"""Welcome {username}! I'm CredoAI, your AI Loan Advisor. 👋

I see you're interested in our **{selected_loan.get('name', 'loan')}**. Great choice! Let me explain why this could be perfect for you."""
            
            # Format loan amount in Indian currency
            formatted_max_amount = format_indian_currency(selected_loan.get('max_amount', 'N/A'))
            
            loan_details = f"""SELECTED LOAN FOR DETAILED EXPLANATION:
Loan Name: {selected_loan.get('name', 'loan')}
Type: {selected_loan.get('loan_type', 'N/A')}
Interest Rate: {selected_loan.get('min_rate', 'N/A')}%
Max Amount: {formatted_max_amount}
Tenure: {selected_loan.get('min_tenure_months', 'N/A')}-{selected_loan.get('max_tenure_months', 'N/A')} months
Eligibility: {selected_loan.get('eligibility_notes', 'N/A')}
Description: {desc}
Features: {all_features}
Documents needed: {documents_str}"""
            
            system_prompt_explanation = f"""You are CredoAI, a friendly and professional AI Loan Advisor for a fintech platform in India.

{loan_details}

CRITICAL INSTRUCTIONS:
1. You MUST ONLY discuss the {selected_loan.get('name', 'loan')} - this is the loan the user selected
2. Do NOT mention, recommend, or compare with any other loan products
3. Do NOT discuss generic loans or make up loan details
4. ALL information you provide must come from the loan details above
5. Only discuss the features, rates, tenure, eligibility, and documents listed above
6. Do NOT ask about other loans unless the user explicitly requests them

TASK: Provide a comprehensive explanation of ONLY the {selected_loan.get('name', 'loan')} to {username}.

Cover these points using ONLY the information provided above:
1. Why this specific loan is beneficial for the user
2. Key advantages and features (from the list above)
3. Who it's best suited for (based on eligibility criteria)
4. Important terms, conditions and eligibility criteria (from above)
5. Required documents (list what's needed)
6. How to proceed with application

Be conversational, warm, professional and encouraging. Use Indian currency (₹). 
IMPORTANT: Use ONLY the loan details provided - do NOT add information about other loans or generic loan types."""
            
            detailed_explanation = ""
            try:
                print(f"📝 Generating AI explanation for {selected_loan.get('name', 'loan')}...")
                explanation_response = client.chat.completions.create(
                    model="meta-llama/llama-3-8b-instruct",
                    messages=[
                        {"role": "system", "content": system_prompt_explanation},
                        {"role": "user", "content": f"Please provide a comprehensive explanation of the {selected_loan.get('name', 'loan')} and how it could benefit me."}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                detailed_explanation = explanation_response.choices[0].message.content
                print(f"✅ AI Explanation generated successfully: {len(detailed_explanation)} characters")
            except Exception as e:
                print(f"❌ AI explanation error: {str(e)}")
                # Fallback explanation with structured content - use ONLY selected loan data
                fallback_type = selected_loan.get('loan_type', 'loan')
                fallback_desc = selected_loan.get('description', f'This is our {selected_loan.get("name", "loan")} offering.')
                fallback_formatted_amount = format_indian_currency(selected_loan.get('max_amount', 'N/A'))
                
                detailed_explanation = f"""## {selected_loan.get('name', 'Loan')} - Detailed Overview

### What is this loan?
{fallback_desc}

### 💪 Key Advantages & Features:
{chr(10).join(['• ' + f for f in selected_loan.get('features', ['Premium features available'])])}

### 💰 Loan Terms & Conditions:
• **Interest Rate:** {selected_loan.get('min_rate', 'N/A')}% per annum
• **Loan Amount:** Up to {fallback_formatted_amount}
• **Tenure:** {selected_loan.get('min_tenure_months', 'N/A')} to {selected_loan.get('max_tenure_months', 'N/A')} months
• **Loan Type:** {fallback_type.title()}"

### 👥 Who Should Apply?
{selected_loan.get('eligibility_notes', 'Please check eligibility criteria with our team')}

### 📋 Documents Required:
{chr(10).join(['• ' + doc for doc in selected_loan.get('documents_needed', ['Standard KYC documents'])])}

### ✨ Why Choose This Loan?
This {fallback_type} loan is designed to provide you with quick access to funds while maintaining competitive rates and flexible tenure options. It's perfect if {fallback_desc.lower()}

### 🚀 Next Steps:
Feel free to ask me any questions about this loan. I'm here to help you understand every aspect and guide you through the application process!"""
            
            # Store initial conversation with the explanation
            sessions[session_id]["messages"] = [
                {"role": "user", "content": f"Tell me about the {selected_loan.get('name', 'loan')}"},
                {"role": "assistant", "content": detailed_explanation}
            ]
            
            # Store loan details for follow-up context
            sessions[session_id]["loan_details"] = loan_details
            sessions[session_id]["selected_loan_name"] = selected_loan.get('name', 'loan')
            
            # Return ONLY the AI-generated explanation (it includes greeting already)
            print(f"✅ Returning initial response with explanation")
            return {
                "response": detailed_explanation,
                "extra": "",
                "action": None
            }
        else:
            greeting = "Welcome! I'm CredoAI, your AI Loan Advisor. 👋\n\nWhat type of loan are you looking for today? I can help you find the perfect fit."
            sessions[session_id]["messages"] = []
            
            return {
                "response": greeting,
                "extra": "",
                "action": None
            }

    session = sessions[session_id]
    messages = session["messages"]
    data = session["user_data"]
    selected_loan = session.get("selected_loan") or selected_loan

    user_input = req.message
    
    # Process user input
    if user_input.strip():
        print(f"📨 User input received: {user_input[:50]}...")
        messages.append({"role": "user", "content": user_input})

        # Extract income if mentioned
        income = extract_income(user_input)
        if income: 
            data["income"] = income

    # Build loan context for the response
    loan_context = ""
    if selected_loan:
        formatted_context_amount = format_indian_currency(selected_loan.get('max_amount', 'N/A'))
        loan_context = f"""

CONTEXT - USER SELECTED THIS LOAN: {selected_loan.get('name', 'loan')}
Loan Details: {selected_loan.get('loan_type', 'N/A')} | Interest Rate: {selected_loan.get('min_rate', 'N/A')}% | Max Amount: {formatted_context_amount} | Tenure: {selected_loan.get('min_tenure_months', 'N/A')}-{selected_loan.get('max_tenure_months', 'N/A')} months
Features: {', '.join(selected_loan.get('features', []))}  "
Eligibility: {selected_loan.get('eligibility_notes', 'N/A')}"""
    
    # Use appropriate system prompt based on mode
    if session["step"] == "loan_explanation" and selected_loan:
        formatted_system_amount = format_indian_currency(selected_loan.get('max_amount', 'N/A'))
        system_prompt = f"""You are CredoAI, a friendly and professional AI Loan Advisor for a fintech platform in India.

SELECTED LOAN FOR THIS CONVERSATION:
{loan_products}

USER'S SELECTED LOAN DETAILS:
Loan Name: {selected_loan.get('name', 'loan')}
Type: {selected_loan.get('loan_type', 'N/A')}
Interest Rate: {selected_loan.get('min_rate', 'N/A')}%
Max Amount: {formatted_system_amount}
Tenure: {selected_loan.get('min_tenure_months', 'N/A')}-{selected_loan.get('max_tenure_months', 'N/A')} months
Eligibility: {selected_loan.get('eligibility_notes', 'N/A')}
Features: {', '.join(selected_loan.get('features', []))}  "
Documents Needed: {', '.join(selected_loan.get('documents_needed', []))}
Description: {selected_loan.get('description', 'N/A')}

{loan_context}

CRITICAL INSTRUCTIONS FOR THIS CONVERSATION:
1. You are ONLY discussing the {selected_loan.get('name', 'loan')} - this is the loan the user selected
2. Do NOT mention, recommend, or compare with any other loan products
3. Do NOT suggest alternative loans
4. All answers must be about the {selected_loan.get('name', 'loan')} ONLY
5. If user asks about other loans, politely decline and redirect to the selected loan
6. Use ONLY the loan details provided above - do NOT add generic information about other loan types
7. Address user {username} professionally

RESPONSE GUIDELINES:
- Be warm, conversational, and professional
- Provide detailed, accurate answers about the selected loan
- Answer questions about features, rates, tenure, eligibility, documents, and application process
- Use Indian currency format (₹)
- Give practical, actionable advice
- Encourage user to ask questions about THIS loan
- If user wants to apply, guide them to next steps
- Do NOT ask for personal information like name, PAN, Aadhaar, SSN"""
    else:
        system_prompt = f"""You are CredoAI, a friendly and professional AI Loan Advisor for a fintech platform in India.

AVAILABLE LOAN PRODUCTS:
{loan_products}

INSTRUCTIONS:
- Be warm and conversational, like a helpful bank advisor
- Address user {username} professionally (they're already logged in)
- Help users explore and understand loan products FROM THE LIST ABOVE
- Only discuss loans that exist in the available products list
- Answer questions about features, rates, eligibility, documents
- Use Indian currency format (₹)
- Do NOT ask for personal information like name, PAN, Aadhaar, SSN
- Do NOT make up or discuss loans not in the available products list
- Focus on understanding their loan needs and providing guidance
- Recommend suitable loan products from the list when appropriate
- Keep responses concise but helpful"""

    print(f"🤖 Preparing AI response...")
    print(f"   Session step: {session['step']}")
    print(f"   Messages in history: {len(messages)}")
    print(f"   Selected loan: {selected_loan.get('name', 'loan') if selected_loan else 'None'}")
    
    response = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages
        ]
    )

    bot_reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": bot_reply})
    
    print(f"✅ AI response generated: {len(bot_reply)} characters")

    extra = ""

    return {
        "response": bot_reply,
        "extra": extra
    }