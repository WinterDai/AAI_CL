1/16/26, 2:55 PM JedAI Integration with LangChain & pydantic format - JEDAI - Confluence

# ~~**JedAI Integration with LangChain & pydantic format**~~

[Created by Zhe Shuang, last updated by Moqi Zhang on Nov 16, 2025 • 3 minute read](https://wiki.cadence.com/confluence/display/~zshuang)

## 1, How to use langchain_openai through JedAI endpoint


from langchain_openai import ChatOpenAI
import requests
import getpass


[jedai_url = "http://sjf-dsgdspr-084:5668"](http://sjf-dsgdspr-084:5668/)
password=getpass.getpass("password:")
token = requests.post(
f"{jedai_url}/api/v1/security/login", headers={"Content-Type": "application/json"},
json={"username": getpass.getuser(), "password": password, "provider": "LDAP"}
).json()["access_token"]


LOCAL_LLM_BASE_URL = f"{jedai_url}/api/copilot/v1/llm"
LOCAL_LLM_API_KEY = token
# change the model name
LOCAL_LLM_MODEL_NAME = ""


llm = ChatOpenAI(
openai_api_base=LOCAL_LLM_BASE_URL,
openai_api_key=LOCAL_LLM_API_KEY,
model_name=LOCAL_LLM_MODEL_NAME,
temperature=0.7,
max_tokens=256
)
messages = "what is llm?"
response = llm.invoke(messages)
print("Response from local LLM:")
print(response.content)

|on-prem|Llama3.1_JEDAI_MODEL_CHAT_2|LOCAL_LLM_MODEL_NAME = "Llama3.1_JEDAI_MODEL_CHAT_2"|
|---|---|---|
|cloud|AzureOpenAI|LOCAL_LLM_MODEL_NAME = "AzureOpenAI"|
||Claude|LOCAL_LLM_MODEL_NAME = "Claude"|
||GEMINI|LOCAL_LLM_MODEL_NAME = "GEMINI"|
||GCP_OSS|LOCAL_LLM_MODEL_NAME = "gcp_oss"|



2, How to use langchain_openai with 'with_structured_output'


**[Support status: http://sjf-dsgdspr-084:5000 (e-version)](http://sjf-dsgdspr-084:5000/)**







|Col1|Col2|Col3|Fully Support|Supported with<br>ChatPromptTemplate<br>workaround|
|---|---|---|---|---|
|On_prem||on_prem_nvidia/llama-3_3-nemotron-super-<br>49b-v1_5|Yes||
|||on_prem_Llama3.3_JEDAI_MODEL_CHAT_2|Yes||
|||on_prem_Llama3.1_JEDAI_MODEL_CHAT_2|Yes||
|||on_prem_openai/gpt-oss-120b|Yes||
|||on_prem_Qwen3-32B|Yes||
||AzureOpenAI|AzureOpenAI_gpt-4o|Yes||
|||AzureOpenAI_o4-min|Yes||
|||AzureOpenAI_gpt-5|Yes||
|||AzureOpenAI_gpt-5-mini|Yes||


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018885/JedAI+Integration+with+LangChain+pydantic+format 1/4


1/16/26, 2:55 PM JedAI Integration with LangChain & pydantic format - JEDAI - Confluence














|Col1|Col2|Col3|Col4|Col5|
|---|---|---|---|---|
|||AzureOpenAI_gpt-5-2|Yes||
||||||
|||~~AzureOpenAI_rnd01-gpt4-vision~~|~~Yes~~||
||Claude|GCP_claude-sonnet-4 (series)|GCP_Claude not support structured output|Yes|
||Gemini|GCP_gemini-2.5-pro  (series)|Yes (25.13-e009)||
|||GCP_gemini-2.5-flash|Yes (25.13-e009)||
|||GCP_gemini-2.5-flash-lite|Yes (25.13-e009)||
||GCP_OSS|GCP_openai/gpt-oss-120b-maas|Yes (25.13-e009)||
|||GCP_openai/gpt-oss-120b-maas|Yes (25.13-e009)||
|||GCP_meta/llama-3.1-70b-instruct-maas|Yes (25.13-e009)||
|||GCP_meta/llama-3.3-70b-instruct-maas|Yes (25.13-e009)||
|||GCP_meta/llama-4-scout-17b-16e-instruct-<br>maas|Yes (25.13-e009)||
|||GCP_meta/llama-3.1-405b-instruct-maas|Yes (25.13-e009)||
|||GCP_deepseek-ai/deepseek-r1-0528-maas|Yes (25.13-e009)||
||AWSBedrock|AWSBedrock_amazon.titan-text-lite-v1|\||
|||AWSBedrock_amazon.titan-text-express-v1|\||
|||AWSBedrock_anthropic.claude-3-haiku-<br>20240307-v1:0|Yes (25.13-e009)||
|||AWSBedrock_anthropic.claude-3-opus-<br>20240229-v1:0|Yes (25.13-e009)||
|||AWSBedrock_anthropic.claude-3-5-haiku-<br>20241022-v1:0|Yes (25.13-e009)||
|||AWSBedrock_anthropic.claude-3-5-sonnet-<br>20241022-v2:0|Yes (25.13-e009)||
|||AWSBedrock_us.anthropic.claude-3-7-<br>sonnet-20250219-v1:0|Yes (25.13-e009)||
|||AWSBedrock_us.anthropic.claude-sonnet-4-<br>20250514-v1:0|Yes (25.13-e009)||
|||AWSBedrock_us.anthropic.claude-opus-4-<br>20250514-v1:0|Yes (25.13-e009)||
|||AWSBedrock_us.anthropic.claude-opus-4-1-<br>20250805-v1:0|Yes (25.13-e009)||



JedAI now supports the structured output functionality in LangChain. This feature allows models to generate structured outputs easily, facilitating data processing and
integration. However, it is important to note that different models handle this functionality differently.


Special Cases for Claude and Gemini Models(GPT_OSS_120b as well)


For GCP Claude (Anthropic) models, due to their inherent design characteristics, GCP does not support the **direct** use of the with_structured_output feature.


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018885/JedAI+Integration+with+LangChain+pydantic+format 2/4


1/16/26, 2:55 PM JedAI Integration with LangChain & pydantic format - JEDAI - Confluence


**To ensure that Claude models can return structured data, we need to use LangChain’s ChatPromptTemplate module to design specific prompts that constrain**
**the model to produce outputs in the expected structured format.**


Example Code: Using ChatPromptTemplate for Structured Output


import os
import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


LOCAL_LLM_BASE_URL = f"{jedai_url}/api/copilot/v1/llm"
LOCAL_LLM_API_KEY = token


######## **create llm model using langchain_openai** #############


def create_llm(model_name):
return ChatOpenAI(
openai_api_base=LOCAL_LLM_BASE_URL,
openai_api_key=LOCAL_LLM_API_KEY,
model_name=model_name,
max_tokens=256
)


############### **define return json format** ##################


class PersonInfo(BaseModel):
"""Information about a person."""
name: str = Field(description="The full name of the person")
age: int = Field(description="The age of the person")


################ **with_structured_output #** ##################
model_name = 'Claude'
llm = create_llm(model_name)


llm_with_structured_output = llm.with_structured_output(PersonInfo)
prompt = ChatPromptTemplate.from_messages([
(


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018885/JedAI+Integration+with+LangChain+pydantic+format 3/4


1/16/26, 2:55 PM JedAI Integration with LangChain & pydantic format - JEDAI - Confluence


"system",
"""You are a helpful assistant that extracts information about people from text.
Your task is to identify the name and age of the person mentioned in the text.
Return the extracted information as a JSON object that conforms to the following schema:
{schema}

~~IMPORTANT: Return ONLY valid JSON without any markdown formatting or code blocks.~~
Do not include ```json or ``` in your response.
"""
),
("human", "Please extract the person's information from the following text:\n\n{text_input}")
])


chain = prompt | llm_with_structured_output


user_text = """
My friend Alice is 30 years old. She works as a software engineer.
"""


try:
print(f"Calling LLM ({model_name}) to extract structured information...")
result = chain.invoke({
"schema": PersonInfo.model_json_schema(),
"text_input": user_text
})
print(f"\n--- Extraction Successful for {model_name} ---")
print(f"Type of result: {type(result)}")
[print(f"Name: {result.name}")](http://result.name/)
print(f"Age: {result.age}")
return True

except Exception as e:
print(f"\n--- An error occurred during extraction for {model_name} ---")
print(f"Error: {e}")
print("This might happen if the LLM failed to generate valid JSON or a JSON that conforms to the schema.")


No labels


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018885/JedAI+Integration+with+LangChain+pydantic+format 4/4


