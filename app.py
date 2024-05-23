import streamlit as st
import numpy as np
import random
import time
from PIL import Image
import os
import mimetypes
from supabase import create_client, Client, StorageException
from io import StringIO, BytesIO
from tempfile import NamedTemporaryFile


# check if image
def is_image(file_path):
	try:
		Image.open(file_path)
		return True
	except IOError:
		return False

def get_supabase_client():
	url = st.secrets['supabase_url']
	key = st.secrets['supabase_key']
	supabase = create_client(url, key)
	return supabase

# check if file already exists
def check_supabase_file_exists(file_path):
	supabase = get_supabase_client()
	bucket_name = st.secrets["bucket_name"]
	supabase_storage_ls = supabase.storage.from_(bucket_name).list()
	
	if any(file["name"] == os.path.basename(file_path) for file in supabase_storage_ls):
		return True
	else:
		return False


def upload_file_to_supabase_storage(file_obj):
	base_name = os.path.basename(file_obj.name)
	path_on_supastorage = os.path.splitext(base_name)[0] + '_' + str(round(time.time())//600)  + os.path.splitext(base_name)[1]
	mime_type, _ = mimetypes.guess_type(file_obj.name)
	
	supabase = get_supabase_client()
	bucket_name = st.secrets["bucket_name"]
	
	bytes_data = file_obj.getvalue()
	with NamedTemporaryFile(delete=False) as temp_file:
		temp_file.write(bytes_data)
		temp_file_path = temp_file.name
	
	try:
		with open(temp_file_path, "rb") as f:
			if check_supabase_file_exists(path_on_supastorage):
				public_url = supabase.storage.from_(bucket_name).get_public_url(path_on_supastorage)
			else:
				supabase.storage.from_(bucket_name).upload(file=temp_file_path, path=path_on_supastorage, file_options={"content-type": mime_type})
				public_url = supabase.storage.from_(bucket_name).get_public_url(path_on_supastorage)
	except StorageException as e:
		print("StorageException:", e)
		raise
	finally:
		os.remove(temp_file_path)  # Ensure the temporary file is removed
	
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
		public_url = upload_file_to_supabase_storage(uploaded_file)
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

