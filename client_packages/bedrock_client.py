import os
import yaml
import boto3
from yaml.loader import SafeLoader
from datetime import datetime, timezone


class KnowledgeBaseChat:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)  # Go up one level
        config_path = os.path.join(parent_dir, "config", "config.yaml")
        with open(config_path) as file:
            self.config = yaml.load(file, Loader=SafeLoader)
        self.aws_region = self.config["bedrock_configuration"].get("aws_region", None)
        self.account_id = self.config["bedrock_configuration"].get("account_id", None)
        self.session = boto3.Session(region_name=self.aws_region)
        self.bedrock_agent_runtime_client = self.session.client("bedrock-agent-runtime", region_name=self.aws_region)

    @staticmethod
    def add_references(input_text, citations):
        citations = sorted(citations, key=lambda x: x["end"])
        output_text = input_text
        offset = 0
        reference_counter = 1
        references = []

        for pos in citations:
            end = pos["end"]
            count = len(pos["reference"])
            actual_end = end + offset
            reference_string = "".join([f'<a href="#ref-{reference_counter + i}" target="_self">[{reference_counter + i}]</a>' for i in range(count)])
            output_text = output_text[:actual_end] + reference_string + output_text[actual_end:]
            for index, value in enumerate(pos["reference"]):
                references.append(
                    {
                        "id": reference_counter + index,
                        "text": value["content"]["text"],
                        "source": value["location"]["s3Location"]["uri"],
                        "metadata": value["metadata"],
                    }
                )
            offset += len(reference_string)
            reference_counter += count

        # output_text = output_text.replace("$", "\$")
        return output_text, references

    def stream_data(self, kb_response):
        citations = []
        session_id = None
        op_steam = []

        if session_id is None and "sessionId" in kb_response:
            session_id = kb_response["sessionId"]

        if "stream" in kb_response:
            op_steam = kb_response["stream"]

        full_text = ""
        for event in op_steam:
            if "output" in event:
                text = event["output"]["text"]
                full_text += text
            if "citation" in event:
                citations.append(event["citation"]["citation"])

        text_pieces = []
        for citation in citations:
            text_piece = {
                "start": citation["generatedResponsePart"]["textResponsePart"]["span"]["start"],
                "end": citation["generatedResponsePart"]["textResponsePart"]["span"]["end"],
                "reference": citation["retrievedReferences"],
            }
            text_pieces.append(text_piece)

        output_text, references = self.add_references(full_text, text_pieces)
        return session_id, output_text, references

    def chat_with_model(self, br_session_id, new_text, generation_prompt=None, orchestration_prompt=None):
        cfg = self.config["bedrock_configuration"]
        cfg_orchestration = cfg.get("orchestration_config", {})
        cfg_generation = cfg.get("generation_config", {})

        inference_model_id = cfg.get("inference_model_id", None)
        rerank_model_id = cfg.get("rerank_model_id", None)
        kb_id = cfg.get("kb_id", None)
        search_type = cfg.get("search_type", None)
        n_source_chunks = cfg.get("n_source_chunks", None)
        n_re_ranked_docs = cfg.get("n_re_ranked_docs", None)
        generation_max_tokens = cfg_generation.get("model_config", {}).get("max_tokens", None)
        generation_temp = cfg_generation.get("model_config", {}).get("temp", None)
        generation_top_p = cfg_generation.get("model_config", {}).get("top_p", None)
        orchestration_max_tokens = cfg_orchestration.get("model_config", {}).get("max_tokens", None)
        orchestration_temp = cfg_orchestration.get("model_config", {}).get("temp", None)
        orchestration_top_p = cfg_orchestration.get("model_config", {}).get("top_p", None)
        query_split_type = cfg.get("bedrock_query_split_type", None)
        guardrail_id = cfg.get("guardrail_id", None)
        guardrail_version = cfg.get("guardrail_version", None)
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Input Params
        generation_prompt = generation_prompt.replace("{current_time}", current_time)
        orchestration_prompt = orchestration_prompt.replace("{current_time}", current_time)

        generation_model_arn = f"arn:aws:bedrock:{self.aws_region}:{self.account_id}:inference-profile/{inference_model_id}"
        rerank_model_arn = f"arn:aws:bedrock:{self.aws_region}::foundation-model/{rerank_model_id}"

        # print("Inside br call", br_session_id)

        # Build vectorSearchConfiguration
        vector_search_config = {
            "overrideSearchType": search_type,
            "numberOfResults": n_source_chunks,
            "rerankingConfiguration": {
                "bedrockRerankingConfiguration": {
                    "modelConfiguration": {
                        "modelArn": rerank_model_arn,
                    },
                    "numberOfRerankedResults": n_re_ranked_docs,
                },
                "type": "BEDROCK_RERANKING_MODEL",
            },
        }

        # Build the main configuration
        knowledge_base_config = {
            "knowledgeBaseId": kb_id,
            "modelArn": generation_model_arn,
            "generationConfiguration": {
                "inferenceConfig": {
                    "textInferenceConfig": {
                        "maxTokens": generation_max_tokens,
                        "temperature": generation_temp,
                        "topP": generation_top_p,
                    }
                },
                "promptTemplate": {"textPromptTemplate": f"""{generation_prompt}"""},
            },
            "retrievalConfiguration": {"vectorSearchConfiguration": vector_search_config},
            "orchestrationConfiguration": {
                "inferenceConfig": {
                    "textInferenceConfig": {"maxTokens": orchestration_max_tokens, "temperature": orchestration_temp, "topP": orchestration_top_p}},
                "promptTemplate": {
                    "textPromptTemplate": f"""{orchestration_prompt}"""
                },
                "queryTransformationConfiguration": {"type": query_split_type},
            },
        }

        if cfg.get("enable_guardrails"):
            knowledge_base_config["generationConfiguration"]["guardrailConfiguration"] = {"guardrailId": guardrail_id, "guardrailVersion": guardrail_version}

        retrieve_and_generate_config = {"type": "KNOWLEDGE_BASE", "knowledgeBaseConfiguration": knowledge_base_config}

        # Build the arguments for the function call
        kwargs = {"input": {"text": new_text}, "retrieveAndGenerateConfiguration": retrieve_and_generate_config}

        # Conditionally add sessionId if available
        if br_session_id is not None:
            kwargs["sessionId"] = str(br_session_id)

        # Call the function
        response = self.bedrock_agent_runtime_client.retrieve_and_generate_stream(**kwargs)

        # Process the streaming data
        br_session_id, text_with_references, citations = self.stream_data(response)

        return br_session_id, text_with_references, citations
