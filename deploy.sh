#!/bin/bash
# Purpose: To deploy the App to Cloud Run.

# Google Cloud Project ID
PROJECT=ptransformers

# Google Cloud Region
LOCATION=us-central1

# Deploy app from source code
gcloud run deploy llm-chat-application --source . --region=$LOCATION --project=$PROJECT --allow-unauthenticated