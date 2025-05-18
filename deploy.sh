#!/bin/bash
# Purpose: To deploy the App to Cloud Run.

# Google Cloud Project ID
PROJECT=ptransformers

# Google Cloud Region
LOCATION=us-central1

# Load environment variables from .env file
source .env

# Deploy app from source code
gcloud run deploy llm-chat-application \
  --source . \
  --region=$LOCATION \
  --project=$PROJECT \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,ES_URL=$ES_URL,ES_API_KEY=$ES_API_KEY