import os
import yaml
import streamlit as st
from pathlib import Path
import streamlit_authenticator as stauth

script_dir: Path = Path(__file__).parent  # Go up one level
parent_dir: Path = script_dir.parent  # Go up one level
config_path: Path = parent_dir / "config/config.yaml"
# Open the YAML file
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)
authenticator.login()

if st.session_state["authentication_status"]:
    with st.sidebar:
        st.write(f":material/account_circle: {st.session_state['name']}")
    authenticator.logout("Logout", "sidebar")
    chat_page = st.Page("chatbot.py", title="Home", icon=":material/login:")
    pg = st.navigation([chat_page])
    pg.run()
elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")
elif authenticator.register_user('Register user', preauthorization=False):
    st.success('User registered successfully')
