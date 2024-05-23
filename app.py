import streamlit as st
import numpy as np
import random
import time
from PIL import Image
import os

# check if image
def is_image(file_path):
    try:
        Image.open(file_path)
        return True
    except IOError:
        return False

from supabase import create_client, Client
def get_supabase_client():
    url = st.secrets['supabase_url']
    key = st.secrets['supabase_key']
    supabase = create_client(url, key)
    return supabase

def upload_file_to_supabase_storage(file_path):
    path_on_supastorage = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)

    supabase = get_supabase_client()
    bucket_name = st.secrets["bucket_name"]
    with open(file_path, 'rb') as f:
        supabase.storage.from_(bucket_name).upload(file=f,path=path_on_supastorage, file_options={"content-type": mime_type})
    
    public_url = supabase.storage.from_(bucket_name).get_public_url(path_on_supastorage)
    return public_url



st.title("Echo Bot")

# Initialize chat history
if "messages" not in st.session_state:
	st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
	with st.chat_message(message["role"]):
		st.markdown(message["content"])


# Define response function
# Streamed response emulator
def response_generator():
	response = random.choice(
	[
            "Hello there! How can I assist you today?",
            "Hi, human! Is there anything I can help you with?",
            "Do you need help?",
        ]
	)
	for word in response.split():
		yield word + " "
		time.sleep(0.05)

# upload file
with st.sidebar:
	uploaded_file = st.file_uploader("Upload File!")
	if uploaded_file is not None:
		# display filename
		# st.write("Filename:", uploaded_file.name)
		public_url = upload_file_to_supabase_storage(uploaded_file.name)
		print(public_url)
		if uploaded_file.type.startswith("image/"):
			st.image(uploaded_file)


# React to user input
if prompt := st.chat_input("What is up?"):
	# Display user message in chat message container
	with st.chat_message("user"):
		st.markdown(prompt)
    # Add user message to chat history
	st.session_state.messages.append({"role": "user", "content": prompt})
	
	# Display assistant response in chat message container
	with st.chat_message("assistant"):
		response = st.write_stream(response_generator())
	# Add assistant response to chat history
	st.session_state.messages.append({"role": "assistant", "content": response})

