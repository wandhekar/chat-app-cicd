import streamlit as st
import requests
import json
import time
from typing import Dict, Any

# Streamlit page configuration
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# Hugging Face API configuration
HF_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
# Alternative models you can try:
# "microsoft/DialoGPT-large"
# "facebook/blenderbot-400M-distill"
# "microsoft/DialoGPT-small"

def query_huggingface(payload: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
    """
    Query Hugging Face Inference API with retry logic
    """
    headers = {
        "Content-Type": "application/json",
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # Model is loading, wait and retry
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    st.warning(f"Model is loading... Retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                st.warning(f"Request failed, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(1)
                continue
            else:
                st.error(f"Request failed: {str(e)}")
                return {"error": str(e)}
    
    return {"error": "Max retries exceeded"}

def get_ai_response(user_input: str) -> str:
    """
    Get AI response from Hugging Face model
    """
    payload = {
        "inputs": user_input,
        "parameters": {
            "max_length": 100,
            "temperature": 0.7,
            "do_sample": True,
            "pad_token_id": 50256
        }
    }
    
    result = query_huggingface(payload)
    
    if "error" in result:
        return f"Sorry, I encountered an error: {result['error']}"
    
    try:
        # Extract the generated text
        if isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get("generated_text", "")
            # Remove the input from the response if it's included
            if generated_text.startswith(user_input):
                response = generated_text[len(user_input):].strip()
            else:
                response = generated_text.strip()
            
            return response if response else "I'm not sure how to respond to that."
        else:
            return "I didn't get a proper response. Please try again."
            
    except Exception as e:
        return f"Error processing response: {str(e)}"

def main():
    # App header
    st.title("🤖 AI Chat Assistant")
    st.markdown("---")
    
    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ About")
        st.write("This is a simple chat interface using:")
        st.write("- **Frontend**: Streamlit")
        st.write("- **LLM**: Hugging Face DialoGPT")
        st.write("- **Deployment**: Kubernetes + CI/CD")
        
        st.markdown("---")
        st.header("🔧 Configuration")
        st.write(f"**Model**: DialoGPT-medium")
        st.write(f"**Status**: {'🟢 Online' if True else '🔴 Offline'}")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_response(prompt)
                st.write(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Built with Streamlit 🚀 | Powered by Hugging Face 🤗"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()