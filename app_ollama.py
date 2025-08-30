import streamlit as st
import requests
import json
import time
from typing import Dict, Any

# Streamlit page configuration
st.set_page_config(
    page_title="AI Chat Assistant - Ollama",
    page_icon="🦙",
    layout="wide"
)

# Ollama API configuration
# Use environment variable or default to localhost for development
import os
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_API_URL = f"http://{OLLAMA_HOST}:11434/api/generate"

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        url = f"http://{OLLAMA_HOST}:11434/api/tags"
        print(f"Checking Ollama status at: {url}")  # Debug line
        response = requests.get(url, timeout=5)
        return {
            "reachable": response.status_code == 200,
            "status_code": response.status_code,
            "body": response.text
        }
    except requests.exceptions.RequestException as e:
        return {
            "reachable": False,
            "error": str(e)
        }


def get_available_models():
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"http://{OLLAMA_HOST}:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except:
        return []

def query_ollama(user_input: str, model: str = "llama3.2:1b") -> str:
    """
    Query Ollama local LLM
    """
    try:
        payload = {
            "model": model,
            "prompt": user_input,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 150
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response generated.")
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to Ollama. Please make sure Ollama is installed and running."
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. The model might be processing a complex query."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def get_ai_response(user_input: str, model: str) -> str:
    """
    Get AI response from local Ollama model
    """
    return query_ollama(user_input, model)

def main():
    # App header
    st.title("🦙 AI Chat Assistant - Ollama")
    st.markdown("---")
    
    # Check Ollama status
    ollama_status = check_ollama_status()
    available_models = get_available_models()
    
    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ About")
        st.write("This is a simple chat interface using:")
        st.write("- **Frontend**: Streamlit")
        st.write("- **LLM**: Ollama (Local)")
        st.write("- **Deployment**: Kubernetes + CI/CD")
        
        st.markdown("---")
        st.header("🔧 Configuration")
        
        # Model selection
        if available_models:
            selected_model = st.selectbox(
                "Select Model:",
                available_models,
                index=0 if available_models else None
            )
        else:
            selected_model = "llama3.2:1b"
            st.write(f"**Model**: {selected_model}")
        
        st.write(f"**Ollama Status**: {'🟢 Online' if ollama_status else '🔴 Offline'}")
        
        if not ollama_status:
            st.error("⚠️ Ollama is not running!")
            st.write("**Setup Instructions:**")
            st.code("# 1. Install Ollama from ollama.ai")
            st.code("# 2. Start Ollama service\nollama serve")
            st.code("# 3. Pull a model\nollama pull llama3.2:1b")
            
        st.markdown("---")
        
        # Model info
        if ollama_status and available_models:
            st.write(f"**Available Models:** {len(available_models)}")
            for model in available_models[:3]:  # Show first 3
                st.write(f"• {model}")
            if len(available_models) > 3:
                st.write(f"• ... and {len(available_models) - 3} more")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Main chat area
    if not ollama_status:
        st.warning("🔴 Ollama is not running. Please start Ollama to begin chatting.")
        st.info("See the sidebar for setup instructions.")
    else:
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
                with st.spinner("🤔 Thinking..."):
                    response = get_ai_response(prompt, selected_model)
                    st.write(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Built with Streamlit 🚀 | Powered by Ollama 🦙 | Local AI Chat"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()