import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

st.title("🤖 AI Loan Agent")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your AI Loan Assistant.\n\nHow can I help you today?"
        }
    ]

if "user_data" not in st.session_state:
    st.session_state.user_data = {}



if st.button("🔄 Start New Application"):
    st.session_state.messages = []
    st.session_state.user_data = {}
    st.rerun()


for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    system_prompt = """You are CredoAI, a friendly and professional AI Loan Advisor for a fintech platform in India.

INSTRUCTIONS:
- Be warm and conversational, like a real bank agent
- Help users explore and understand different loan products
- Answer questions about loan features, rates, eligibility criteria
- Provide loan amounts in Indian currency (₹)
- Do NOT ask for personal information like name, PAN, Aadhaar, or ID numbers
- Focus on understanding user's loan needs
- Recommend suitable loan products
- Keep responses concise and helpful"""

    # =========================
    # 🤖 AI RESPONSE
    # =========================

    with st.chat_message("assistant"):
        with st.spinner("Processing your loan request..."):
            response = client.chat.completions.create(
                model="meta-llama/llama-3-8b-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *st.session_state.messages
                ]
            )

            bot_reply = response.choices[0].message.content
            st.write(bot_reply)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})