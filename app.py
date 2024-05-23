import streamlit as st
import numpy as np
import random
import time

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


col1,col2 = st.columns([0.2,0.8])

with col1:
	uploaded_file = st.file_uploader("Upload File!")
	if uploaded_file is not None:
	    # display filename
	    # st.write("Filename:", uploaded_file.name)
	    if uploaded_file.type.startswith("image/"):
	        st.image(uploaded_file)
					   
with col2:
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

