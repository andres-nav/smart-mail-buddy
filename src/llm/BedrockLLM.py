import json
from typing import Any

import boto3

from .AbstractLLM import AbstractLLM


class BedrockLLM(AbstractLLM):
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
    ) -> None:
        self.client = boto3.client(
            service_name="bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def _query(self, query: str) -> str:
        """Send a query to AWS Bedrock's Llama 3 70B model."""
        try:
            body = self._format_request_body(query)
            response = self._invoke_model(body)
            return self._parse_response(response)
        except Exception as e:
            raise RuntimeError(f"Bedrock API call failed: {str(e)}") from e

    def _format_request_body(self, query: str) -> str:
        # Handle both text and multimodal queries
        messages = [{"role": "user", "content": [{"type": "text", "text": query}]}]

        return json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "messages": messages,
            }
        )

    def _invoke_model(self, body: str) -> dict[str, Any]:
        response = self.client.invoke_model(
            body=body,
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            accept="application/json",
            contentType="application/json",
        )
        return json.loads(response["body"].read().decode())

    def _parse_response(self, response: dict[str, Any]) -> str:
        if "content" not in response or len(response["content"]) == 0:
            raise ValueError("Invalid Bedrock response format")
        return response["content"][0]["text"].strip()
