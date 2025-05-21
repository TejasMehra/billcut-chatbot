import streamlit as st
import google.generativeai as genai
import os

# --- API Key Loader ---
def get_api_key():
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("Please set the GOOGLE_API_KEY in Streamlit secrets or environment.")
            return None
        return api_key

# --- Gemini Setup ---
api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)
else:
    st.stop()

# --- System Prompt ---
system_prompt = """
You are Sophie, a helpful and friendly AI assistant for BillCut — a company that helps people in India get out of debt.

Your tone is:
- Friendly
- Fun and a bit quirky
- Supportive and to-the-point

Your job:
- Explain how BillCut helps with loans, EMIs, debt settlement, and money habits.
- Use short, clear sentences.
- Bring the conversation back to BillCut when possible.
- Let the user lead — end the conversation naturally without forcing lines like “Want me to explain in detail?”
- Always respond in the same language the user is using — English, Hindi or Hinglish.

Never start replies with “Hi” or “Hey”.
"""

# --- Scripted Responses ---
faq_responses = {
    "what is billcut": "BillCut is a fintech company that does debt refinancing. Want to know more?",
    "does billcut charge": "BillCut doesn’t charge any fees, except ₹19 for a session with our advisor during debt settlement.",
    "interest rate": "The interest rate is usually between 12 to 19 percent.",
    "multiple loans": "Yes! You can combine all your loans into one and pay directly via NBFC.",
    "how does billcut pay": "BillCut works with NBFCs. They pay your loan amount directly.",
    "will the funds come": "Yes! Funds come to your account — except in balance transfers, which use a demand draft.",
    "foreclosure charge": "It's around 3% of the remaining amount.",
    "credit score": "Nope! Your score won’t be affected — unless you go for debt settlement.",
    "why work email": "Just to verify your job — we won’t send any mails there, promise!",
    "what is demand draft": "It's like a prepaid cheque — but safer, and it can’t bounce.",
    "what are nbfc": "NBFCs give loans like banks — but they’re not banks.",
    "full form of nbfc": "NBFC stands for Non-Banking Financial Company.",
    "how does billcut pay credit card": "BillCut pays your card via its lending partners."
}

# Longer follow-ups
detailed_followups = {
    "what is billcut": "BillCut helps refinance your debt through its lending partners — like converting credit card dues into EMIs. We also offer debt settlement.",
    "how does billcut pay credit card": "BillCut pays your credit card bill by transferring funds to your account through its lending partners. The amount is converted into a low-interest EMI. You just show proof of payment for your credit card."
}

# Soft repeat fallback
repeat_followups = {
    "what is billcut": "To recap — BillCut can turn your high-interest loans into manageable EMIs. We even negotiate with banks. Want help with your own case?",
    "how does billcut pay credit card": "Again — funds go from our partners to your account. You pay the card and repay in EMIs. Want to explore options?"
}

# --- Streamlit App UI ---
st.title("👋 Hi, how can I help you today?")
st.caption("talk to me in whatever language you like: english, hindi or a mixture of both maybe...")

# --- Session State ---
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",
        system_instruction=system_prompt
    )
    st.session_state.chat = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with BillCut today?"}]

if "last_question_key" not in st.session_state:
    st.session_state.last_question_key = None

if "followup_count" not in st.session_state:
    st.session_state.followup_count = 0

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input Logic ---
if user_input := st.chat_input("Ask me anything about BillCut..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    input_lower = user_input.lower().strip()
    response = None

    if input_lower in ["yes", "yeah", "sure", "ok", "okay"]:
        key = st.session_state.last_question_key
        count = st.session_state.followup_count

        if key:
            if count == 0 and key in detailed_followups:
                response = detailed_followups[key]
                st.session_state.followup_count += 1
            elif count == 1 and key in repeat_followups:
                response = repeat_followups[key]
                st.session_state.followup_count += 1
            else:
                try:
                    response = st.session_state.chat.send_message(user_input).text
                except Exception as e:
                    response = "Oops! Something went wrong. Try again?"
                    print("Gemini error:", e)
        else:
            try:
                response = st.session_state.chat.send_message(user_input).text
            except Exception as e:
                response = "Oops! Something went wrong. Try again?"
                print("Gemini error:", e)

    else:
        match = None
        for key in faq_responses:
            if key in input_lower:
                match = key
                break

        if match:
            response = faq_responses[match]
            st.session_state.last_question_key = match
            st.session_state.followup_count = 0
        else:
            try:
                response = st.session_state.chat.send_message(user_input).text
            except Exception as e:
                response = "Oops! Something went wrong. Try again?"
                print("Gemini error:", e)
            st.session_state.last_question_key = None
            st.session_state.followup_count = 0

    # Display response
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
