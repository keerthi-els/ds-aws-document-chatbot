import uuid
import yaml
import json
import petname
import pandas as pd
import streamlit as st
from pathlib import Path
from client_packages.bedrock_client import KnowledgeBaseChat
from client_packages.utils import replace_bracketed_numbers_with_links, download_s3_file, show_pdf

# Open the YAML file
script_dir: Path = Path(__file__).parent  # Go up one level
parent_dir: Path = script_dir.parent  # Go up one level
config_path: Path = parent_dir / "config/config.yaml"
data_source_path = parent_dir / "data/"
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# INITs
kb_class = KnowledgeBaseChat()
unique_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "generation_prompt" not in st.session_state:
    st.session_state.generation_prompt = config["bedrock_configuration"]["generation_config"]["prompt"]
if "orchestration_prompt" not in st.session_state:
    st.session_state.orchestration_prompt = config["bedrock_configuration"]["orchestration_config"]["prompt"]
if "session_name" not in st.session_state:
    st.session_state.session_name = petname.Generate(2, separator="-")

chat_container = st.container()
input_text = st.chat_input("Ask questions about your data")

if input_text:
    # Init
    unique_id = uuid.uuid4()

    # Append new query to chat history and display it immediately
    st.session_state.chat_history.append({"role": "user", "text": input_text, "unique_id": unique_id})

# Re-render the chat history (Streamlit re-runs this script, so need this to preserve previous chat messages)
for i, message in enumerate(st.session_state.chat_history):  # loop through the chat history
    # renders a chat line for the given role, containing everything in the with block
    with chat_container.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["text"])

        if message["role"] == "assistant":
            # Display bot response with document references
            bot_response = message["text"]

            # Display the text with references
            st.markdown(bot_response, unsafe_allow_html=True)

            if len(message["references"]) > 0:
                st.markdown("###### 📑 Citations: ")

                # Create columns for each reference
                columns = st.columns(len(message["references"]))

                # Display the references in expanders within columns
                for idx, ref in enumerate(message['references']):
                    source_id = ref['id']
                    with columns[idx].popover(f'[{source_id}]'):
                        st.markdown(ref['text'].replace("$", "\$"), unsafe_allow_html=True)
                        print(ref["source"])
                        file_name = ref["source"].split('/')[-1]
                        if str(file_name).endswith(".pdf"):
                            if st.button(file_name, key=file_name + str(i) + str(idx)):
                                file_path = download_s3_file(ref["source"], data_source_path)
                                if "/" in file_path:
                                    show_pdf(file_path)
                                    st.button(
                                        "close pdf",
                                        key="close " + file_name + str(i) + str(idx),
                                    )
                                else:
                                    st.write(file_path)
                        if str(file_name).endswith(".json"):
                            if st.button(file_name, key="json" + file_name + str(i) + str(idx)):
                                file_path = download_s3_file(ref["source"], data_source_path)
                                if "/" in file_path:
                                    with open(file_path, "r") as f:
                                        data = json.load(f)
                                    st.json(data)
                                    st.button(
                                        "close json",
                                        key="json close " + file_name + str(i) + str(idx),
                                    )
                                else:
                                    st.write(file_path)
                        if str(file_name).endswith(".csv"):
                            if st.button(file_name, key="csv" + file_name + str(i) + str(idx)):
                                file_path = download_s3_file(ref["source"], data_source_path)
                                if "/" in file_path:
                                    st.dataframe(pd.read_csv(file_path))
                                    st.button("close csv", key="close " + file_name + str(i) + str(idx))
                                else:
                                    st.write(file_path)

# Fetch the response and update the chat history
if input_text:
    with st.spinner("Retrieving AI response...", show_time=True):
        session_id, full_text, citations = kb_class.chat_with_model(
            br_session_id=st.session_state.session_id,
            new_text=input_text,
            generation_prompt=st.session_state.generation_prompt,
            orchestration_prompt=st.session_state.orchestration_prompt,
        )

        # Store details in session
        st.session_state.session_id = session_id
        st.session_state.chat_history.append({"role": "assistant",
                                              "text": replace_bracketed_numbers_with_links(full_text, "#"),
                                              'references': citations,
                                              "unique_id": unique_id,
                                              "session_id": st.session_state.session_id})

        # Re-run the script to display the assistant's response
        st.rerun()

with st.sidebar:
    st.divider()
    # Sidebar input for session name (user can edit)
    session_name = st.text_input(
        "Session Name",
        value=st.session_state.session_name,
        max_chars=50
    )

    # Update session state if user changes the name
    st.session_state.session_name = session_name

    # Export Chat
    if st.session_state.chat_history:
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.session_id = None
            st.session_state.session_name = petname.Generate(2, separator="-")
            st.rerun()

    st.divider()
    with st.expander("Prompt options"):
        st.subheader("Generation Prompt")
        prompt_toggle = st.toggle("Edit Default Prompt")
        generation_prompt = st.text_area(
            r"""Below is the default prompt. Do not remove '\$search_results\$' while editing prompt as it is 
            mandatory for proper execution """,
            st.session_state.generation_prompt,
            height=200,
            disabled=not prompt_toggle,
            help="When using a custom prompt, ensure it includes concise and clear instructions",
        )
        # Save session info
        st.session_state.generation_prompt = generation_prompt

        st.subheader("Orchestration Prompt")
        orche_prompt_toggle = st.toggle("Edit Default Prompt", key="orche")
        orchestration_prompt = st.text_area(
            """Below is the default prompt. Do not remove '\$conversation_history\$,\$output_format_instructions\$' 
            while editing prompt as these are mandatory for proper execution """,
            st.session_state.orchestration_prompt,
            height=200,
            disabled=not orche_prompt_toggle,
            help="When using a custom prompt, ensure it includes concise and clear instructions",
            key="orche_text",
        )
        # Save session info
        st.session_state.orchestration_prompt = orchestration_prompt
