import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
# FIX: Sahi import path use kiya hai jo latest LangChain support karta hai
from langchain_core.prompts import ChatPromptTemplate 
from dotenv import load_dotenv

# Environment variables load karein
load_dotenv()

# 1. FAISS Index Load karein
DB_PATH = "bank_policy_index"

# Embeddings model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# FAISS DB load logic
if os.path.exists(DB_PATH):
    vector_db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
else:
    vector_db = None
    print("🚨 FAISS Index not found!")

# 2. LLM Setup (FIX: Naya model name add kiya hai jo decommission nahi hua)
llm = ChatGroq(
    model="llama-3.3-70b-versatile", # Ye naya aur fast model hai
    temperature=0.1,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# 3. System Prompt Template (Aapka purana prompt)
SYSTEM_PROMPT = """
Aap BOP Digital Bank ke ek Smart AI Assistant hain. 
Aapka kaam user ki madad karna hai unki banking activities aur bank policies ke mutabiq.

USER CONTEXT:
- Name: {user_name}
- Current Balance: Rs. {balance}
- Recent Activities: {activities}

KNOWLEDGE BASE (PDF Rules):
{pdf_context}

RULES:
1. Agar user bank policy ka pooche, toh Knowledge Base se jawab dein.
2. Agar user apni activity ya balance ka pooche, toh USER CONTEXT use karein.
3. Sirf banking se mutaliq jawab dein. 
4. Jawab hamesha Urdu (Hinglish) aur English ka mix (Professional) hona chahiye.
5. Agar koi cheez context mein nahi hai, toh kahein "I am sorry, mujhe is bare mein maloomat nahi hai."

User query: {query}
"""

def generate_smart_response(user_query, user_profile, recent_activities):
    """Context-Aware response generation function."""
    
    # 1. Knowledge Base (Vector Search)
    pdf_context = ""
    if vector_db:
        try:
            docs = vector_db.similarity_search(user_query, k=3)
            pdf_context = "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"Search Error: {e}")

    # 2. Activities Formatting
    activities_str = ", ".join(recent_activities) if recent_activities else "No recent activities found."

    # 3. Prompt Construction
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    chain = prompt | llm

    # 4. Response Generation
    try:
        response = chain.invoke({
            "user_name": user_profile.get('f_name', 'User'),
            "balance": user_profile.get('balance', 0.0),
            "activities": activities_str,
            "pdf_context": pdf_context,
            "query": user_query
        })
        return response.content
    except Exception as e:
        # User-friendly error
        return f"I'm sorry, system mein thora masla aa raha hai. Error: {str(e)}"