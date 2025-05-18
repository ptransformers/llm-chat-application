import streamlit as st
from google.cloud import storage  # Import GCS client

# Page configuration
st.set_page_config(page_title="Update Prompts", page_icon="✏️")

# header
st.title("Update Prompts")

st.write(
    "Use the form below to update the prompts to pass it as side input to pipeline"
)
# Initialize GCS client
client = storage.Client()


def upload_prompt_to_gcs(bucket_name, file_name, content):
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_string(content)
        return True
    except Exception as e:
        st.error(f"An error occurred while uploading to GCS: {e}")
        return False


def read_prompt_from_gcs(bucket_name, file_name):
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)

        if blob.exists():
            content = blob.download_as_text()
            return content
        else:
            return ""
    except Exception as e:
        st.error(f"An error occurred while reading from GCS: {e}")
        return ""


# GCS configuration
GCS_BUCKET_NAME = "pt-prompt-templates"
GCS_FILE_NAME = "new_prompt.txt"

# Read existing prompt from GCS
existing_prompt = read_prompt_from_gcs(GCS_BUCKET_NAME, GCS_FILE_NAME)
print(existing_prompt)

# Form for updating prompts
with st.form(key="prompt_update_form"):
    # Input for new prompt, pre-filled with existing prompt
    new_prompt = st.text_area(
        "Enter the new prompt:", value=existing_prompt, height=150
    )

    # Submit button
    submit_button = st.form_submit_button("Update Prompt")

    if submit_button:
        if new_prompt:
            # Upload prompt to GCS
            success = upload_prompt_to_gcs(GCS_BUCKET_NAME, GCS_FILE_NAME, new_prompt)
            if success:
                st.success("Prompt updated and uploaded to GCS successfully!")
        else:
            st.error("Please enter a valid prompt.")
