import os  # Add this import for environment variables
import json
import random

import requests
import streamlit as st
from dotenv import load_dotenv
from google.cloud import aiplatform
from google.cloud import pubsub_v1
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_google_vertexai import VertexAI

from openai import OpenAI
from elasticsearch import Elasticsearch
import os

TEMPERATURE = 0.7
MAX_TOKENS = 1024

# Load environment variables
load_dotenv()

# Google Cloud Pub/Sub configuration
PUBSUB_PROJECT_ID = "ptransformers"
PUBSUB_TOPIC_ID = "user-conversation"
# Create a publisher client
publisher = pubsub_v1.PublisherClient()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Elasticsearch configuration
ES_URL = os.getenv("ES_URL")
ES_API_KEY = os.getenv("ES_API_KEY")
es = Elasticsearch(
    ES_URL,
    api_key=ES_API_KEY,
)

# Page configuration
st.set_page_config(page_title="LLM Chat Application", page_icon="🤖")

# App header
st.title("🤖 LLM Chat Application")


# Function to generate random User-Agent
def get_random_user_agent():
    """Generate a random User-Agent string"""
    # List of common browsers
    browsers = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 "
        "Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 "
        "Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 "
        "Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0",
        "Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/109.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 "
        "Safari/605.1.15",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 "
        "Safari/537.36 Edg/109.0.1518.78",
        # Opera
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 "
        "Safari/537.36 OPR/95.0.0.0",
    ]

    return random.choice(browsers)


# Function to publish message to Google Cloud Pub/Sub
def publish_to_pubsub(user_message, ai_response):
    """
    Publish chat message to Google Cloud Pub/Sub

    Args:
        user_message (str): The user's message
        ai_response (str): The AI's response
    """
    try:
        topic_path = publisher.topic_path(PUBSUB_PROJECT_ID, PUBSUB_TOPIC_ID)

        # Create message payload
        message_data = {"user": user_message, "agent": ai_response}

        # Convert the message to JSON and encode as bytes
        message_bytes = json.dumps(message_data).encode("utf-8")

        # Publish the message
        future = publisher.publish(topic_path, data=message_bytes)
        message_id = future.result()

        print(f"Message published to Pub/Sub with ID: {message_id}")
        print(f"Message content: {message_data}")
        return True
    except Exception as e:
        print(f"Error publishing to Pub/Sub: {e}")
        return False


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


def get_query_vector(input_text: str):
    response = client.embeddings.create(
        input=input_text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def search_top_conversation(vector):
    print("started to search")
    try:
        response = es.search(
            index="user_insights",
            knn={
                "field": "conversation_vector",
                "query_vector": vector,
                "k": 1,
                "num_candidates": 10
            },
            source=["conversation"]
        )

        hits = response['hits']['hits']
        print(hits)
        if hits:
            return hits[0]['_source'].get('conversation')
        else:
            return None

    except Exception as e:
        print("Search error:", e)
        return None


# Get IP and user agent using external service
def get_client_info():
    """Get client IP address and user agent using external service"""
    try:
        # Generate a random User-Agent for this request
        random_user_agent = get_random_user_agent()

        # Use ipify API to get IP address
        ip_response = requests.get(
            "https://api.ipify.org?format=json",
            timeout=5,
            headers={"User-Agent": random_user_agent},
        )
        ip_data = ip_response.json()
        ip_address = ip_data.get("ip", "Unknown")

        # Get additional IP info with the same random User-Agent
        geo_response = requests.get(
            f"https://ipapi.co/{ip_address}/json/",
            timeout=5,
            headers={"User-Agent": random_user_agent},
        )
        geo_data = geo_response.json()

        client_info = {
            "ip_address": ip_address,
            "city": geo_data.get("city", "Unknown"),
            "region": geo_data.get("region", "Unknown"),
            "country": geo_data.get("country_name", "Unknown"),
            # Include the random User-Agent in the client info
            "user_agent": random_user_agent,
        }
        return client_info
    except Exception as e:
        print(f"Error getting client info: {e}")
        return {
            "ip_address": "Unknown",
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "user_agent": "Unknown",
        }


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
    print("-" * 50)
    print(f"User Info : {get_client_info()}")

    # Publish the conversation to Google Cloud Pub/Sub
    publish_to_pubsub(user_message, ai_response)

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

                    #  Embed the user query
                    query_vector = get_query_vector(prompt)

                    #  Search similar past conversation
                    similar_convo = search_top_conversation(query_vector)

                    print(similar_convo)

                    # If found, inject it into memory
                    if similar_convo:
                        st.session_state.conversation.memory.chat_memory.add_user_message(
                            f"Related Info Retrieved from Memory : {similar_convo}"
                        )
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
