import os

import streamlit as st
from dotenv import load_dotenv
from google.cloud import aiplatform
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_google_vertexai import VertexAI


TEMPERATURE = 0.7
MAX_TOKENS = 1024

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="LLM Chat Application", page_icon="🤖")

# App header
st.title("🤖 LLM Chat Application")


# Google Cloud authentication setup
def initialize_vertex_ai():
    # Set Google Cloud project ID and region
    project_id = "ptransformers"  # Hardcoded project ID
    region = "us-central1"  # Hardcoded region

    try:
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=region)
        return project_id, region
    except Exception as e:
        st.error(f"Error initializing Vertex AI: {str(e)}")
        st.info("Please check if your Google Cloud authentication is properly set up.")
        return None, None


# Callback function that runs after receiving a response
def on_response_received(user_message, ai_response):
    """
    This function is called after receiving a response from the AI.
    You can add any post-processing logic here.

    Args:
        user_message (str): The user's message
        ai_response (str): The AI's response
    """
    # Log the conversation (example callback action)
    print(f"User: {user_message}")
    print(f"AI: {ai_response}")

    # You can add more logic here, such as:
    # - Sentiment analysis on the response
    # - Storing conversation in a database
    # - Triggering other actions based on the content
    # - etc.


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation" not in st.session_state:
    memory = ConversationBufferMemory(return_messages=True)
    st.session_state.conversation = None  # Initially set to None

# Initialize the model at startup instead of using a sidebar
if st.session_state.conversation is None:
    try:
        # Initialize Vertex AI
        project_id, region = initialize_vertex_ai()

        if project_id and region:
            # Set default model parameters
            model_name = "gemini-2.0-flash-lite-001"
            temperature = TEMPERATURE
            max_tokens = MAX_TOKENS

            # Set up LLM model
            llm = VertexAI(
                model_name=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens,
                project=project_id,
                location=region,
            )

            # Create conversation chain
            memory = ConversationBufferMemory(return_messages=True)
            st.session_state.conversation = ConversationChain(
                llm=llm, memory=memory, verbose=True
            )

            st.success(f"Model {model_name} loaded successfully!")
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        st.info("Check error details and verify your Google Cloud settings.")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Enter your message"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check if LLM is configured
    if st.session_state.conversation is None:
        with st.chat_message("assistant"):
            st.error(
                "Failed to initialize the AI model. Please check the error messages."
            )
    else:
        # Show loading state
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Send question to LLM
                    response = st.session_state.conversation.predict(
                        input=prompt)
                    st.markdown(response)
                    # Save response
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )

                    # Call the callback function after receiving the response
                    on_response_received(prompt, response)

                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
                    st.info(
                        "Please verify that Vertex AI API is enabled and you have appropriate permissions."
                    )
