# Setting Up Your Knowledge Base

To enable the project to work correctly, you need to upload your documents to an S3 bucket and create a knowledge base linked to that bucket. Please follow the steps below:

## 1. Upload Documents to S3 Bucket

- Upload your documents (e.g., PDFs, text files, etc..) to your designated Amazon S3 bucket.

## 2. Create a Knowledge Base

- Follow the instructions in the [AWS Bedrock documentation on creating a knowledge base](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-create.html).

- During creation, configure the following:
    - Link the knowledge base to the S3 bucket containing your documents.
    - Use **Opensearch serverless** database as your vector store.
    - **Embedding Method:** Choose an embedding strategy suitable for your data (e.g., OpenAI embeddings, custom embeddings).
    - **Chunking Strategy:** Define how your documents are split into chunks (e.g., by sentence, paragraph, fixed size).

- After successfully creating the knowledge base, copy the **Knowledge Base ID**.

## 3. Update the Configuration File

- Open the project's configuration file `config.yaml` under config folder.
- Locate the placeholder `"kb_id"` in the file.
- Fill the `"kb_id"` with the actual Knowledge Base ID you copied in Bedrock.

```plaintext
# Example:
kb_id: your-fetched-kb-id
```

## 4. Finalize and Run

- Save the configuration file.
- Proceed with running your project as per the setup instructions.

---

**Note:** If you need assistance with creating the knowledge base or configuring the embedding and chunking strategies, please refer to [AWS platform's documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-build.html).

---