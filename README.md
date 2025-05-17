# LLM Chat Application

## Overview

This application is a conversational chatbot powered by Google Cloud Vertex AI's Gemini models. It provides a
user-friendly web interface built with Streamlit and manages conversation context using LangChain.

## Prerequisites

- Python 3.9+
- Google Cloud account with Vertex AI API enabled
- Google Cloud authentication set up

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm-chat-app.git
   cd llm-chat-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Google Cloud authentication:
   ```bash
   gcloud auth application-default login
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Configuration

The application uses the following configuration:

- Model: `gemini-2.0-flash-lite-001`
- Temperature: 0.7 (controls randomness)
- Max tokens: 1024 (maximum response length)

You can modify these parameters in the `app.py` file.

## License

[MIT License](LICENSE)
