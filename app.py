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
import json
import requests


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

# insert data to database
def supabase_insert_message(user_message,response_content,messages,content_type,service_channel):
    supabase = get_supabase_client()
    data, count = supabase.table('messages').insert({"user_message": user_message, "response_content": response_content,"messages":messages,"content_type":content_type,"service_channel":service_channel}).execute()

def supabase_insert_user(name,user_name,profile,picture,oauth_token):
    supabase = get_supabase_client()
    data, count = supabase.table('users').insert({"name":name,"user_name":user_name,"profile":profile,"picture":picture,"oauth_token":oauth_token}).execute()


def supabase_fetch_user(user_name):
    supabase = get_supabase_client()
    data,count = supabase.table('users').select("*").eq('user_name',user_name).execute()
    return data
        

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



# Define response function
def get_completion(messages):     
	
	# headers
	openai_api_key = st.secrets['openai_api_key']
	base_url = st.secrets['base_url']
	headers = {
	  'Authorization': f'Bearer {openai_api_key}'
	}

	temperature = 0.7
	max_tokens = 2048
	print(messages)
	# request body
	data = {
		'model': 'gpt-4o',  # we use gpt-4o here
		'messages': messages,
		'temperature':temperature, 
		'max_tokens':max_tokens,
		'stream':True,
		# 'stream_options':{"include_usage": True}, # retrieving token usage for stream response
	}

	# get response with stream
	response = requests.post(base_url, headers=headers, json=data,stream=True)
	response_content = ""
	for line in response.iter_lines():
		line = line.decode().strip()
		if line == "data: [DONE]":
			continue
		elif line.startswith("data: "):
			line = line[6:] # remove prefix "data: "
			try:
				data = json.loads(line)
				if "delta" in data["choices"][0]:
					content = data["choices"][0]["delta"].get("content", "")
					# response_content += content
					# yield response_content
					yield content
			except json.JSONDecodeError:
				print(f"Error decoding line: {line}")

	# print(response_content)
	# print('-----------------------------------\n')
	# response_data = {}
    

# save file to session
if 'uploaded_file' not in st.session_state:
	st.session_state.uploaded_file = None

# upload file
with st.sidebar:
	uploaded_file = st.file_uploader("Upload File!")
	if uploaded_file is not None:
		# display filename
		# st.write("Filename:", uploaded_file.name)
		st.session_state.uploaded_file = uploaded_file
		public_url = upload_file_to_supabase_storage(uploaded_file)
		if uploaded_file.type.startswith("image/"):
			st.image(uploaded_file)
	else:
		public_url = ''

st.title("ChatGPT-4o")

# Initialize chat history
if "messages" not in st.session_state:
	st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
	# if user message, display user content and user image(if uploaded)
	if message["role"] == 'user':
		with st.chat_message(message["role"]):
			st.markdown(message['content'][0]['text'])
		# display user image in history
		image_urls = [item['image_url']['url'] for item in message['content'] if item['type'] == 'image_url']
		if image_urls:
			st.image(image_urls[0])
	else:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])



system_message = '''You are GPT-4o("o" for omni), OpenAI's new flagship model that can reason across audio, vision, and text in real time. 
GPT-4o matches GPT-4 Turbo performance on text in English and code, with significant improvement on text in non-English languages, while also being much faster. 
GPT-4o is especially better at vision and audio understanding compared to existing models.
GPT-4o's text and image capabilities are avaliable for users now. More capabilities like audio and video will be rolled out iteratively in the future.
'''


prompt = st.chat_input("What is up?")

# React to user input
if prompt:
	# Display user message in chat message container
	with st.chat_message("user"):
		st.markdown(prompt)
	user_content = [{"type": "text", "text": prompt}]
	content_type = 'text'
	# if uploaded image, display in message list and remove from sidebar
	if public_url:
		st.image(public_url)
		# st.session_state.uploaded_file = None
		content_image = {
			"type": "image_url",
			"image_url": {
				"url": public_url,
			},}
		user_content.append(content_image)
		content_type = 'image'
	st.session_state.uploaded_file = None
	public_url = ''
	user_message = [{"role": "user", "content": user_content}]
	history_messages = st.session_state.messages
	system_message = [{"role": "system", "content": system_message}]
	
	#system message + latest 2 round dialogues + user input
	messages = system_message + history_messages[-4:] + user_message
	
	# Display assistant response in chat message container
	with st.chat_message("assistant"):
		response_content = st.write_stream(get_completion(messages))
		
	# Add user message to chat history
	st.session_state.messages.append({"role": "user", "content": user_content})
	# Add assistant response to chat history
	st.session_state.messages.append({"role": "assistant", "content": response_content})

	# insert messages to database
	supabase_insert_message(user_message,response_content,messages,content_type,service_channel="streamlit")




