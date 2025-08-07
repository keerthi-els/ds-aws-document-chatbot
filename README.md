# AWS Document Chatbot

This project is a starter template for a Retrieval-Augmented Generation (RAG) chatbot designed for quick and efficient interaction with your documents. By uploading your data to an S3 bucket and creating a linked knowledge base, users can bypass the initial setup time and rapidly build upon this foundation to develop custom methods and features.

Under the hood, the system leverages AWS Bedrock's Retrieve and Generate API to communicate seamlessly with the Bedrock knowledge base. It includes an integrated response formatting system that presents answers with proper citations and references. When a user clicks on a referenced document in the response, the system automatically fetches the corresponding document directly from S3 into a local data folder, enabling easy review and validation.

The configuration is largely pre-set, with most Bedrock parameters ready except for the `knowledge_base_id` (kb_id), which users need to input after creating their knowledge base. Additionally, the platform allows for direct editing of prompts—both the orchestration prompt (to fetch data) and the generation prompt (to produce responses)—via the Streamlit interface or within the configuration file. This flexibility enables users to test and refine prompts interactively without restarting the application or modifying the codebase.

Overall, this template provides a streamlined, customizable starting point for building document-based chatbots with minimal setup, making it ideal for rapid prototyping and iterative development.

## Prerequisites

- **Create your knowledge base** by following the instructions in the [Setting Up Your Knowledge Base](./knowledge_base_setup.md) guide.
- Git installed on your system
- Python 3.x installed on your system
- **`uv`** installed (if not already available). To install `uv`, follow the official installation instruction:[UV Installation Guide](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)

## Setup Instructions

### 1. Clone the repository into your project folder

```bash
git clone https://github.com/elsevier-research/ds-nsf-aws-rag.git
```

### 2. Navigate to the project folder

```bash
cd path/to/your/project_folder
```

### 3. Create a virtual environment

```bash
uv venv
```

### 4. Activate the virtual environment

- On **MacOS/Linux**:

```bash
source venv/bin/activate
```

- On **Windows**:

```bash
source venv\Scripts\activate
```

### 5. Synchronize your environment. This will install all the required packages.

```bash
uv sync
```

### 6. Get the project directory path

```bash
pwd
```

Copy the output path.

### 7. Set the `PYTHONPATH` environment variable

Replace `your_copied_path` with the path you copied:

```bash
export PYTHONPATH="your_copied_path"
```

## 4. Set AWS Credentials

- Ensure your system has the necessary AWS credentials to access S3 and Bedrock services.
- You can do this by:

  - **Setting environment variables** for AWS credentials:

    ```bash
    export AWS_ACCESS_KEY_ID=your_access_key_id
    export AWS_SECRET_ACCESS_KEY=your_secret_access_key
    export AWS_SESSION_TOKEN=your_session_token  # if using temporary credentials
    ```

  - **Or** by attaching an IAM role to your system with the required permissions for S3 and Bedrock.

### 8. Run the Streamlit app

```bash
streamlit run streamlit_app/main.py
```

---

## Notes

- Ensure all dependencies are installed in your virtual environment.
- For Windows users, use Command Prompt or PowerShell for commands.
- To deactivate the virtual environment, run:

```bash
deactivate
```

