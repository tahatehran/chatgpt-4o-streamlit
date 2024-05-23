import streamlit as st
import numpy as np

# display user message
with st.chat_message("user"):
	st.write("Hello 👋")

# display assistant message
with st.chat_message("assistant"):
    st.write("Hello human")
    st.bar_chart(np.random.randn(30, 3))

# user input
with st.chat_input("Say something") as prompt:
	if prompt:
		st.write(f"User has sent the following prompt: {prompt}")
