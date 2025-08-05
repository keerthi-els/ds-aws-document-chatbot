import re
import os
import yaml
import boto3
import base64
import streamlit as st
from pathlib import Path
from urllib.parse import urlparse

# Open the YAML file
script_dir: Path = Path(__file__).parent  # Go up one level
parent_dir: Path = script_dir.parent  # Go up one level
config_path: Path = parent_dir / "config/config.yaml"
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)


def show_pdf(filepath):
    with open(filepath, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="1000" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def download_s3_file(s3_path, target_folder):
    # Parse the S3 path
    parsed_url = urlparse(s3_path)
    bucket_name = parsed_url.netloc
    key = parsed_url.path.lstrip('/')

    # Initialize S3 client
    s3 = boto3.client('s3')

    # Extract filename from the key
    filename = os.path.basename(key)
    target_path = os.path.join(target_folder, filename)

    try:
        # Check if the object exists
        s3.head_object(Bucket=bucket_name, Key=key)
        # Download the file
        s3.download_file(bucket_name, key, target_path)
        print(f"File downloaded to {target_path}")
        return target_path
    except s3.exceptions.NoSuchKey:
        print("file not found")
        return "file not found"
    except s3.exceptions.ClientError as e:
        # Handle other errors, e.g., 404 Not Found
        if e.response['Error']['Code'] == '404':
            print("file not found")
            return "file not found"
        else:
            print(f"An error occurred: {e}")
            return "An error occurred look at log file"


br_regex: re.Pattern = re.compile(r"(<br ?\/>|&lt;br ?/ ?&gt;)")


def replace_urls_with_hyperlinks(text: str) -> str:
    """Replace URLs in the text with HTML hyperlink tags.

    :param text: The input text containing URLs.
    :return: The modified text with URLs replaced by HTML hyperlinks.
    """
    # Regular expression pattern for matching URLs
    url_pattern = r"(https?://[^\s]+)"

    # Function to replace matched URL with HTML hyperlink
    def replace_with_link(match):
        url = match.group(0)
        # Create HTML hyperlink
        return f'<a href="{url}" target="_blank">{url}</a>'

    # Use re.sub to replace URLs with hyperlinks
    return re.sub(url_pattern, replace_with_link, text)


def clean_html_text(html_text) -> str:
    if not html_text:
        return html_text
    # Escape "$" because in markdown this means the start of an equation.
    result = replace_urls_with_hyperlinks(html_text).replace("$", r"\$")
    result = br_regex.sub("<br>", result)
    return result


def replace_match(match, base_url):
    number = match.group(1)
    return f'<a href="{base_url}{number}">[{number}]</a>'


def replace_bracketed_numbers_with_links(text, base_url):
    pattern = r'\[(\d+)\]'
    replaced_text = re.sub(pattern, lambda match: replace_match(match, base_url), text)
    replaced_text = clean_html_text(replaced_text)
    return replaced_text
