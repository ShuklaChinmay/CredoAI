from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from typing import Optional, Any
from dotenv import load_dotenv
import os
import re
import requests
from fastapi import APIRouter
router = APIRouter()

# load_dotenv(dotenv_path=".env")

# app = FastAPI()

def fetch_loan_products():
    try:
        BASE_URL = os.getenv("BASE_URL")
        res = requests.get(f"{BASE_URL}/loan/products")
        return res.json().get("products", [])
    except Exception as e:
        print("Loan Fetch Error:", e)
        return []

# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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


def format_loan_scheme_overview(loan_products):
    """Format all available loan schemes in a readable format for the user"""
    if not loan_products:
        return "No loan products available"
    
    overview = "📊 **Available Loan Schemes:**\n\n"
    for i, product in enumerate(loan_products, 1):
        max_amount = format_indian_currency(product.get('max_amount', 'N/A'))
        min_rate = product.get('interest_rate', product.get('min_rate', 'N/A'))
        max_tenure = product.get('max_tenure_months', 'N/A')
        
        overview += f"{i}. **{product.get('name', 'Loan')}** ({product.get('loan_type', 'N/A')})\n"
        overview += f"   • Amount: Up to {max_amount}\n"
        overview += f"   • Interest Rate: {min_rate}% p.a.\n"
        overview += f"   • Tenure: Up to {max_tenure} months\n"
        overview += f"   • Min Income: ₹{product.get('residual_income', 25000):,}/month\n\n"
    
    return overview


@router.post("/chat")
def chat(req: ChatRequest):

    session_id = req.session_id
    selected_loan = req.selected_loan
    username = req.username or "there"
    loan_products = fetch_loan_products()

    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "user_data": {"name": username},
            "selected_loan": selected_loan,
            "step": "loan_explanation" if selected_loan else "show_loans",
            "loan_products": loan_products
        }
        
        
        if selected_loan:
            # User came from loan card - show specific loan details
            features_str = ", ".join(selected_loan.get('features', ['N/A'])[:3]) if selected_loan.get('features') else 'N/A'
            desc = selected_loan.get('description', 'A great loan product')
            all_features = ", ".join(selected_loan.get('features', [])) if selected_loan.get('features') else 'N/A'
            documents_str = ", ".join(selected_loan.get('documents_needed', [])) if selected_loan.get('documents_needed') else 'N/A'
            
            greeting = f"""👋 **Welcome, {username}!** I'm CredoAI, your AI Loan Advisor.

I see you're interested in our **{selected_loan.get('name', 'loan')}**. Great choice! Let me explain why this could be perfect for you and answer all your questions."""
            
            # Format loan amount in Indian currency
            formatted_max_amount = format_indian_currency(selected_loan.get('max_amount', 'N/A'))
            
            loan_details = f"""SELECTED LOAN FOR DETAILED EXPLANATION:
Loan Name: {selected_loan.get('name', 'loan')}
Type: {selected_loan.get('loan_type', 'N/A')}
Interest Rate: {selected_loan.get('interest_rate', selected_loan.get('min_rate', 'N/A'))}%
Max Amount: {formatted_max_amount}
Tenure: {selected_loan.get('min_tenure_months', 'N/A')}-{selected_loan.get('max_tenure_months', 'N/A')} months
Min Income Required: ₹{selected_loan.get('residual_income', 'N/A'):,}/month
Processing Fee: {selected_loan.get('processing_fee_pct', 'N/A')}%
Eligibility: {selected_loan.get('eligibility_notes', 'Please contact us for details')}
Description: {desc}
Features: {all_features}
Documents needed: {documents_str}"""
            
            system_prompt_explanation = f"""You are Rajesh Kumar, a seasoned and genuine Loan Advisor at CredoAI with 15+ years of experience helping customers find the perfect financial solutions. You're speaking with {username} - treat them like you would a friend or family member seeking financial advice.

{loan_details}

YOUR PERSONALITY:
- Warm, genuine, and authentically helpful (not robotic)
- Speak like a real person, use conversational language
- Show real understanding of their financial journey
- Empathetic about their needs and concerns
- Patient and never pushy - you're here to guide, not sell
- Confident in your knowledge but humble enough to listen
- Use "I", "we", and "you" naturally in conversation

CRITICAL INSTRUCTIONS:
1. You ONLY discuss the {selected_loan.get('name', 'loan')} - this is what {username} selected
2. Do NOT mention other loans unless {username} specifically asks
3. ALL details come from the provided loan information only
4. Use {username}'s name occasionally (not every sentence) - it builds rapport
5. Do NOT ask for sensitive info like PAN, Aadhaar, SSN, or banking details yet

CONVERSATION STRUCTURE:
1. Open with genuine warmth: "Hi {username}! Great to see you interested in the {selected_loan.get('name', 'loan')}..."
2. Share why THIS loan is particularly suitable for them
3. Walk through key features like you're explaining to a friend
4. Be specific about eligibility - help them understand if they fit
5. Explain documents needed in a reassuring way
6. Invite their questions as a natural conversation

TONE EXAMPLES:
- Instead of: "The loan provides collateral-free borrowing"
  Say: "You won't need to pledge any assets against this loan - it's one of the best parts of it"
  
- Instead of "Processing takes 3-5 days"
  Say: "From the time you submit documents, we typically get you approved within 3-5 days. I've seen approvals in as little as 24 hours for eligible customers"
  
- Instead of "Interest rate is 10.5%"
  Say: "Your interest rate would be 10.5% per annum - which is quite competitive in the market right now"

QUESTIONS TO ASK NATURALLY:
- "Just curious, {username} - how are you planning to use this loan?"
- "Do you have an existing relationship with a bank, or is this new for you?"
- "How soon are you looking to close this? That helps me guide you better."
- "Any concerns or hesitations you'd like to discuss?"

Be like a real advisor - conversational, helpful, and genuinely interested in helping {username} make the right decision. Use contractions (I'm, we've, you're). Make this feel like a real conversation between two people."""
            
            detailed_explanation = ""
            try:
                print(f"📝 Generating AI explanation for {selected_loan.get('name', 'loan')}...")
                explanation_response = client.chat.completions.create(
                    model="meta-llama/llama-3-8b-instruct",
                    messages=[
                        {"role": "system", "content": system_prompt_explanation},
                        {"role": "user", "content": f"Tell me all about the {selected_loan.get('name', 'loan')} and help me understand if it's right for me."}
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
                fallback_rate = selected_loan.get('interest_rate', selected_loan.get('min_rate', 'N/A'))
                
                detailed_explanation = f"""Hey {username}! 👋 

I'm so glad you're interested in our **{selected_loan.get('name', 'loan')}**. Let me tell you why this could be absolutely perfect for you.

## What is the {selected_loan.get('name', 'loan')}?

{fallback_desc} 

In simple terms - this is a {fallback_type} loan that's designed specifically with customers like you in mind. It's straightforward, transparent, and we've helped thousands of people through this exact product.

## Why I Love This Loan for You

Here's what makes this stand out:
{chr(10).join(['• **' + f.split(':')[0] + '** — ' + f if ':' in f else '• ' + f for f in selected_loan.get('features', ['Premium features available'])])}

These aren't just features on paper, {username} - these are genuine benefits that my past clients have really valued.

## The Numbers (The Important Stuff)

- **How much can you borrow?** Up to {fallback_formatted_amount}
- **Interest rate?** Starting at {fallback_rate}% per annum - and honestly, this is quite competitive
- **How long to repay?** You can spread it from {selected_loan.get('min_tenure_months', 'various')} months up to {selected_loan.get('max_tenure_months', 'flexible')} months - so you can tailor it to your budget
- **Processing fee?** {selected_loan.get('processing_fee_pct', 'N/A')}% of the loan amount

The great thing? These are not fixed numbers - depending on your profile, you might qualify for even better terms.

## Who is This Best For?

{selected_loan.get('eligibility_notes', 'We look at your overall financial profile, not just one number')}

Do you fit this picture? I'd love to hear a bit more about your situation.

## What Documents Will You Need?

Good news - it's pretty straightforward:
{chr(10).join(['📄 ' + doc for doc in selected_loan.get('documents_needed', ['Standard KYC documents'])])}

I know documentation can seem intimidating, but these are documents most people already have. We can guide you through every step.

## How Does This Work?

Here's the simple process:
1. **You tell us what you need** - share your goals and situation
2. **We assess your eligibility** - quick and transparent
3. **You submit minimal documents** - nothing crazy, I promise
4. **We verify and approve** - usually within 3-5 days
5. **Money hits your account** - fast and clean

## What Happens Next?

That depends on you, {username}! Here are your options:

👉 **Ask me questions** - Anything you want to know? Go ahead. No such thing as a "stupid question" in the financial world.

👉 **Want details on eligibility?** - Tell me about your situation (income, current obligations) and I can give you a clear sense of what you might qualify for

👉 **Ready to explore further?** - Great! We can start the process and I'll guide you every step of the way

Remember, {username} - I'm here to make this easy for you. My job is to make sure you get the right loan at the right terms. So what would be most helpful for you right now?"""
            
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
            # User hasn't selected a loan yet - show all schemes and guide them
            loan_schemes_overview = format_loan_scheme_overview(loan_products)
            
            greeting = f"""Hi {username}! 👋 I'm **Rajesh Kumar**, your Loan Advisor at CredoAI. 

It's great to meet you! I'm here to make your lending experience smooth, transparent, and tailored to YOUR unique needs. Think of me as your personal financial guide - I'm not here to push products, but to help you find the perfect loan that actually fits your life.

{loan_schemes_overview}

Here's what I'm thinking, {username} - help me understand your situation a bit better so I can guide you to the right loan:

💭 **Tell me:**
- What are you looking to do? (buying a home, car, business expansion, education, or something else?)
- Do you have a ballpark idea of how much you'd need?
- Roughly, what's your monthly income?
- Have you taken loans before, or is this something new for you?

Once I understand your story, I can recommend exactly what'll work best for you - no surprises, no unnecessary back-and-forth.

Looking forward to helping you out! 💪"""
            
            sessions[session_id]["messages"] = []
            sessions[session_id]["step"] = "show_loans"
            
            return {
                "response": greeting,
                "extra": "",
                "action": None
            }

    session = sessions[session_id]
    messages = session["messages"]
    data = session["user_data"]
    selected_loan = session.get("selected_loan") or selected_loan
    loan_products_context = session.get("loan_products", loan_products)

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
Loan Details: {selected_loan.get('loan_type', 'N/A')} | Interest Rate: {selected_loan.get('interest_rate', selected_loan.get('min_rate', 'N/A'))}% | Max Amount: {formatted_context_amount} | Tenure: {selected_loan.get('min_tenure_months', 'N/A')}-{selected_loan.get('max_tenure_months', 'N/A')} months
Features: {', '.join(selected_loan.get('features', []))}
Eligibility: {selected_loan.get('eligibility_notes', 'N/A')}"""
    
    # Use appropriate system prompt based on mode
    if session["step"] == "loan_explanation" and selected_loan:
        formatted_system_amount = format_indian_currency(selected_loan.get('max_amount', 'N/A'))
        system_prompt = f"""You are Rajesh Kumar, a seasoned and empathetic Loan Advisor at CredoAI with 15+ years of experience. You're having an ongoing conversation with {username} about their chosen loan - the {selected_loan.get('name', 'loan')}.

SELECTED LOAN FOR THIS CONVERSATION:
Loan Name: {selected_loan.get('name', 'loan')}
Type: {selected_loan.get('loan_type', 'N/A')}
Interest Rate: {selected_loan.get('interest_rate', selected_loan.get('min_rate', 'N/A'))}%
Max Amount: {formatted_system_amount}
Tenure: {selected_loan.get('min_tenure_months', 'N/A')}-{selected_loan.get('max_tenure_months', 'N/A')} months
Min Monthly Income: ₹{selected_loan.get('residual_income', 'N/A'):,}
Processing Fee: {selected_loan.get('processing_fee_pct', 'N/A')}%
Eligibility: {selected_loan.get('eligibility_notes', 'N/A')}
Features: {', '.join(selected_loan.get('features', []))}
Documents Needed: {', '.join(selected_loan.get('documents_needed', []))}
Description: {selected_loan.get('description', 'N/A')}

CRITICAL RULES:
1. ONLY discuss the {selected_loan.get('name', 'loan')} - never mention other loans
2. If {username} asks about other loans, politely redirect: "Look, I specialize in the {selected_loan.get('name', 'loan')}, and I really think we should focus on making sure this is the right fit for you first. If you'd like to explore other options later, we can absolutely do that."
3. Use ONLY information from the database above - nothing generic
4. Use {username}'s name naturally (every 3-4 exchanges, not every sentence)
5. Never ask for PAN, Aadhaar, SSN, or sensitive banking info at this stage

YOUR PERSONALITY & APPROACH:
- You're like a trusted friend who happens to know loans really well
- Show genuine care about {username}'s financial wellbeing
- Be honest: "Between you and me, this loan is particularly good for your situation because..."
- Use natural language - think conversations, not corporate speak
- Show you're thinking about THEIR future: "What I want for you is..."
- Be patient with questions - there's no rush
- Acknowledge concerns warmly: "That's a fair point, let me explain..."

HOW TO RESPOND:
1. Listen to what {username} is really asking - sometimes it's more than just the surface question
2. Answer in a conversational way with specific examples: "So here's how this works in practice..."
3. Use real context: "Based on what you've told me so far..."
4. Invite more discussion: "Does that make sense? Anything else you're curious about?"
5. Be proactive: "Here's something a lot of people wonder about..." if relevant

GREAT RESPONSES SOUND LIKE:
- "I'm glad you asked that, {username}..."
- "Look, the honest answer is..."
- "Here's what I typically tell people..."
- "You know what? That's actually one of the best things about this loan..."
- "I totally understand why you'd think that, but here's the reality..."
- "From my experience working with hundreds of customers..."

BAD RESPONSES SOUND LIKE:
- "The {selected_loan.get('name', 'loan')} offers..."
- "Per the policy..."
- "As per our terms and conditions..."
- "The applicant must..."

GUIDANCE:
- If they ask about application timeline: "From when you submit everything, we usually have approval within 3-5 days. I've seen approvals in 24 hours for ready customers."
- If they seem hesitant: "I get it - finances can be stressful. But here's what I promise you: we'll make this as simple as possible."
- If they ask about getting better rates: "Your rate depends on your profile - stronger income, better credit history, these things help. But honestly, 8.4% is already a solid rate in the market."
- If they're comparing to competitors: "I respect that you're looking around. All I can tell you is we've built our reputation on treating customers fair and making the process smooth."

ALWAYS REMEMBER: {username} is making an important financial decision. They're trusting you. Be worthy of that trust. Be their advisor first, salesman never."""
    else:
        # Not yet selected a loan - guide them
        loan_products_str = format_loan_scheme_overview(loan_products_context)
        system_prompt = f"""You are Rajesh Kumar, a trusted and experienced Loan Advisor at CredoAI with deep expertise in lending. You're having a friendly, professional conversation with {username} to help them find the PERFECT loan that matches their unique situation.

AVAILABLE LOAN PRODUCTS IN OUR DATABASE:
{loan_products_str}

YOUR APPROACH:
- Be conversational and genuine - like you're chatting with someone while having chai
- Listen carefully to what {username} needs
- Ask thoughtful follow-up questions to understand their situation better
- Provide honest recommendations based on DATABASE LOANS ONLY
- Never force a sale - be their trusted advisor, not a pushy salesman
- Show genuine interest in their financial goals
- Use {username}'s name occasionally to build rapport

CONVERSATION FLOW FOR {username}:
1. Start with a warm greeting and genuine interest in their needs
2. Ask clarifying questions:
   - "What brings you here today? What are you looking to do?"
   - "Do you have a rough idea of how much you might need?"
   - "When would you ideally like to make this happen?"
   - "Have you taken a loan before, or is this your first time?"
3. Based on their answers, recommend suitable options from our DATABASE LOANS
4. Explain WHY each recommended loan is a good fit for THEIR situation
5. Ask if they'd like to dive deeper into any specific loan
6. Once they show interest, provide detailed information about that specific loan

KEY PRINCIPLES:
- ONLY recommend and discuss loans from the database above
- Never make up loans or generic information
- Be specific with numbers and terms - use actual rates, amounts, tenure
- Show empathy: "I understand, many people are in your situation"
- Use conversational language: "So here's what I'm thinking for you..."
- Ask permission: "Would it help if I explained how the approval process works?"
- Be honest: "This loan might be better for your situation because..."

TONE & LANGUAGE:
- Use contractions: "I'm thinking", "You've got", "We'll help"
- Be natural: "Look, based on what you've told me..." instead of "Based on the above criteria..."
- Show personality: "That's a great question!" or "I really like it when people think about this"
- Be warm: "Don't worry, we'll make this simple for you"
- Acknowledge concerns: "I hear you - a lot of people worry about documentation"

EXAMPLE INTERACTIONS:
Instead of: "Our Personal Loan offers unsecured credit up to ₹25,00,000"
Say: "So for a Personal Loan - this is one of my favorites because it's super quick. No need to pledge anything as collateral. You can borrow anywhere from a small amount up to 25 lakhs, and we process it in just a few days usually"

Instead of: "The eligibility criteria includes minimum monthly income of ₹25,000"
Say: "You'd typically need a monthly income of at least 25k, and we look at your overall situation. Have you been working with your current employer for a while?"

Always keep in mind: {username} is a real person with real needs. Be their advisor, their guide, their trusted voice in financial decisions. Make them feel heard, understood, and supported."""

    print(f"🤖 Preparing AI response...")
    print(f"   Username: {username}")
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
    
    # Check if user is switching to a different loan
    user_input_lower = user_input.lower() if user_input else ""
    
    # If currently in loan explanation and user asks about other loans, note it but maintain current focus
    if selected_loan and "other loan" in user_input_lower or "different loan" in user_input_lower or "alternate" in user_input_lower:
        session["asking_about_alternatives"] = True
    
    print(f"✅ AI response generated: {len(bot_reply)} characters")

    extra = ""

    return {
        "response": bot_reply,
        "extra": extra
    }