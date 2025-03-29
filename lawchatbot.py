import streamlit as st
import io
import re
from contextlib import redirect_stdout

from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.wikipedia import WikipediaTools
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv

# Set page configuration as the very first Streamlit command
st.set_page_config(page_title="Indian Law Assistant", layout="wide")

# Load environment variables
load_dotenv()

# Sidebar configuration
st.sidebar.title("Important Legal Resources")
st.sidebar.markdown("**📚 Indian Constitution:** [Read here](https://legislative.gov.in/constitution-of-india/) (English)")
st.sidebar.markdown("**⚖️ Supreme Court of India:** [Visit website](https://www.sci.gov.in/) for judgments and case laws")
st.sidebar.markdown("**⚖️ National Legal Services Authority (NALSA):** [Visit website](https://nalsa.gov.in/) for legal aid services")
st.sidebar.markdown("**⚖️ Legal Services India:** [Visit website](https://legalserviceindia.com/) for legal information and resources")

# Initialize the legal assistant agent with bullet point instructions
legal_agent = Agent(
    name="Indian Law Assistant",
    model=Groq(id="llama-3.2-1b-preview"),
    tools=[WikipediaTools(), DuckDuckGo()],
    instructions=[
        "You are a legal assistant providing general information about Indian government laws.",
        "When a user asks about a specific law or legal matter, identify the relevant Indian laws and provide accurate information.",
        "Format your response as a list of bullet points. For each law or legal matter, include its key provisions, applicability, and relevant sections. For example:",
        "   - **Indian Penal Code (IPC) Section 379:** Deals with theft and prescribes punishment for the offense.",
        "   - **Consumer Protection Act, 2019:** Regulates consumer rights and provides mechanisms for redressal of grievances.",
        "Include a clear disclaimer: 'I am not a lawyer. This information is for general informational purposes only and is not a substitute for professional legal advice, representation, or legal services.'",
        "If the legal matter is complex, advise the user to consult a qualified legal professional.",
        "Encourage the user to seek professional legal assistance for specific cases or legal representation."
    ],
    show_tool_calls=True,
    markdown=True,
)

# Utility functions to clean ANSI escape sequences and box-drawing characters
def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def remove_box_drawing(text):
    box_chars = "┏┓┗┛┃━"
    for ch in box_chars:
        text = text.replace(ch, "")
    return text

def clean_output(text):
    text = strip_ansi_codes(text)
    text = remove_box_drawing(text)
    return text

# Initialize session state for chat history if not already set
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create a placeholder container for the chat history
chat_container = st.empty()

# Function to render chat messages in a fixed-height scrollable container
def display_chat_history():
    chat_html = '<div id="chat-container" style="height: 500px; overflow-y: scroll; padding: 10px; border: 1px solid #ddd;">'
    for message in st.session_state.messages:
        if message["sender"] == "user":
            chat_html += (
                f'<div style="text-align: right; background-color: #DCF8C6; color: black; '
                f'padding: 10px; border-radius: 10px; margin: 5px 0;">{message["text"]}</div>'
            )
        else:
            chat_html += (
                f'<div style="text-align: left; background-color: #F1F0F0; color: black; '
                f'padding: 10px; border-radius: 10px; margin: 5px 0;">{message["text"]}</div>'
            )
    chat_html += '</div>'

    # Add JavaScript to auto-scroll to the bottom when the container is rendered
    scroll_js = """
    <script>
        // Wait for the DOM to be fully loaded
        document.addEventListener("DOMContentLoaded", function() {
            // Get the chat container by its ID
            const chatContainer = document.getElementById("chat-container");
            if (chatContainer) {
                // Scroll to the bottom of the container
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        });
    </script>
    """

    # Combine HTML and JavaScript
    final_html = chat_html + scroll_js

    # Render the combined HTML
    chat_container.markdown(final_html, unsafe_allow_html=True)

# Main UI setup
st.title("Indian Law AI Chatbot")
st.write("Enter your legal query, and get information about relevant Indian government laws as bullet points.")

# Display chat history (this will be updated dynamically in the placeholder)
display_chat_history()

# Input for user's legal query
user_input = st.text_input("Enter your legal query:", key="user_input")

# When the user clicks the button, process input and update chat history
if st.button("Get Legal Information") and user_input:
    # Append user's message to chat history
    st.session_state.messages.append({"sender": "user", "text": user_input})
    
    with st.spinner("Fetching legal information..."):
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                legal_agent.print_response(user_input, stream=True)
            except Exception as e:
                print(f"An error occurred: {e}")
        response = buf.getvalue()
        clean_response = clean_output(response)
        # Append agent's response to chat history
        st.session_state.messages.append({"sender": "bot", "text": clean_response})
    
    # Update the chat container display only once
    display_chat_history()