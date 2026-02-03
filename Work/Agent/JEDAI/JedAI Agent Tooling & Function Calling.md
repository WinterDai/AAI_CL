1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


[Pages /](https://wiki.cadence.com/confluence/collector/pages.action?key=JEDAI&src=breadcrumbs-collector) **…** [/ JedAI Infra Agenda](https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018883/JedAI+Infra+Agenda?src=breadcrumbs-parent)
# JedAI Agent Tooling & Function Calling


[Created by Zhe Shuang, last updated on Dec 22, 2025 • 9 minute read](https://wiki.cadence.com/confluence/display/~zshuang)


Enhanced Agent Support with Unified OpenAI-Compatible InterfaceEnhanced Agent Support with Unified OpenAI-Compatible Interface


We are excited to share a significant update on JedAI's evolution toward comprehensive agent framework support. Our next release introduces robust **Tool Calling capabilities**, establishing a
foundational framework for agent exploration and development.


**Background & Challenges Addressed**



1, Model Format Inconsistencies







Different LLMs present varying input/output formats, making direct API calls cumbersome for users. When developers attempt direct HTTP calls in Python, they must manually adjust
formats for each model, creating unnecessary complexity.(Example see attached figure)


Claude models stream response


GPTs stream response


2, Third-Party Framework Limitations


Popular agent frameworks like **VSCode's Continue plugin** suffer from delayed model support updates.


For instance:


The Vertex API **only** supports Gemini 1.5 in Continue's interface, while we utilize Gemini 2.5 Pro in JedAI.
Claude models via Vertex aren't supported, rendering latest models inaccessible through user-side adaptations.


These limitations necessitate JedAI providing a unified interface for seamless access to cutting-edge models.


**Our Solution: Comprehensive Framework Restructuring**


We've undertaken an extensive architectural overhaul of JedAI's model framework:


1, OpenAI Format Standardization


Implemented the "openai_format" parameter to enable unified input/output formatting
Streamlined API calls for enhanced user convenience and consistency


2, Enhanced Security Compliance


All model API keys remain invisible to users, satisfying IT security requirements


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 1/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


Centralized authentication through JedAI's secure proxy layer


**Practical Implementation Example 1**


Example: VSCode Continue Integration


1, Configuration Setup (config.yaml):


2, Usage Workflows:


**Basic Chat Interaction: Seamless conversation with unified model interface**


**Agent Mode Capabilities:**


**1, Query available Cadence tools: "What tools are available in JedAI-AAI?"**


>>> Query enter, the LLM model will choose which tool to use. The user need **click the accept button.**


>>> Tool use results


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 2/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


**2, Code modification agents: Automated code analysis and modification suggestions(Create a python file in vscode)**


**DeepSeek Integration** : Provides transparent reasoning processes during interactions, offering users insight into model thinking patterns


**Practical Implementation Example 2 (Python)**


Example: jupyter notebook （ python workflow ）


**1, Get access token for JedAI server:**


**By default, JedAI authentication tokens expire after 10 hours.**


**1, Short-Term Login :**


```python
import requests
import getpass
[jedai_url = "http://sjf-dsgdspr-084:5668"](http://sjf-dsgdspr-084:16300/)
token = requests.post(
f"{jedai_url}/api/v1/security/login",
headers={"Content-Type": "application/json"},
json={
"username": getpass.getuser(),
"password": password,
"provider": "LDAP"
}
).json()["access_token"]


headers={"accept": "*/*", "Content-Type": "application/json", "Authorization": f"Bearer {token}"},


# tool


# body


response = requests.post(
api_url,
headers={"accept": "*/*", "Content-Type": "application/json", "Authorization": f"Bearer {token}"},
json=body
)


*** choose different output function ***


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 3/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


**2, Long-Term Login (Non-expiring)**


waiting our next release


**2, Usage Workflows:**


**Prepare you tools function**


Use **openai_format (boolean)**
True: Uses OpenAI-compatible input/output format.
False: Uses model-native format.



|openai_format = True|openai_format = False|Col3|
|---|---|---|
|**Tools**|**Gemini**|**Claude**|
|Tools =  [<br>    {<br>        "type": "function",<br>        "function": {<br>            "name": "get_weather",<br>            "description": "Get current weather, for example<br>beijing weather is sunny",<br>            "parameters": {<br>                "type": "object",<br>                "properties": {<br>                    "location": {"type": "string"}<br>                }<br>            }<br>        }<br>    }<br>]|Tools ={<br>            'tools': [<br>                {<br>                    'function_declarations': [<br>                        {<br>                            'name': 'get_weather',<br>                            'description': 'Get current weather, for<br>example beijing weather is sunny.',<br>                            'parameters': {<br>                                'type': 'object',<br>                                'required': ['location'],<br>                                'properties': {<br>                                    'location': {<br>                                        'type': 'string',<br>                                        'description': 'For example<br>Beijing, Shanghai'<br>                                    }<br>                                }<br>                            }<br>                        }<br>                    ]<br>                }<br>            ]<br>        }|Tools =[<br>    {<br>        'name': 'get_weather',<br>        'description': 'Get current weather, for<br>example beijing weather is sunny',<br>        'input_schema': {<br>            'type': 'object',<br>            'properties': {<br>                "location": {"type": "string"}<br>            },<br>            'required': ['location']<br>        }<br>    }<br>]|


**Model Support Status**






```
      Tool calling capability
      (stream/non-stream)

```











|Deployment|Non-stream|
|---|---|
|`gemini-2.5-pro`|yes|
|`gemini-2.5-flash`|yes|
|`gemini-2.5-flash-lite`|yes|


|Category|Model Name|JedAI Instance|Configuring JedAI Web<br>Copilot:<br>Copilot → Chat Bbx → Copilot<br>Config|
|---|---|---|---|
|`Proprietary`<br>`Commercial`<br>`Models`|`Google Gemini`<br>`(Pro/Flash)`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5668/`|`gemini-2.5-pro:`<br>`project: gcp-cdns-llm-test`<br>`location: us-central1`<br>`deployment: <...>`<br>`1, deployment="gemini-2.5-`<br>`pro"`<br>`2, deployment="gemini-2.5-`<br>`flash"`<br>`3, deployment="gemini-2.5-`<br>`flash-lite"`|
|`Proprietary`<br>`Commercial`<br>`Models`|`Anthropic Claude`<br>`3 (Opus/Sonnet/Haiku)`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5688/`|`claude-sonnet-4:`<br>`project: gcp-cdns-llm-test`<br>`location: us-east5`<br>`deployment: <...>`|


|Deployment|Non-stream|
|---|---|
|`claude-sonnet-4`|yes|
|`claude-3-7-sonnet`|yes|



https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 4/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence




```
Tool calling capability
(stream/non-stream)

```

|Col1|Col2|
|---|---|
|`claude-opus-4-1`|yes|
|`claude-3-5-haiku`|no|
|`claude-3-5-sonnet-v2`|no|








|Deployment|Non-<br>stream|
|---|---|
|`Llama3.1_JEDAI_MODEL_CHAT_2`|yes|
|`Llama3.3_JEDAI_MODEL_CHAT_2`|yes|


|Deployment|Non-<br>stream|
|---|---|
|`nvidia/llama-3_3-`<br>`nemotron-super-49b-v1_5`|yes|







**S**







**S**






|Deployment|Non-stream|Stream|
|---|---|---|
|`Qwen3-32B`|yes|yes|



**S**






|Deployment|Non-<br>stream|
|---|---|
|`deepseek-ai/deepseek-`<br>`v3.1-maas`|no|
|`deepseek-ai/deepseek-r1-`<br>`0528-maas`|yes|


|Category|Model Name|JedAI Instance|Configuring JedAI Web<br>Copilot:<br>Copilot → Chat Bbx → Copilot<br>Config|
|---|---|---|---|
||||`1, deployment="claude-opus-4-`<br>`1"`<br>`2, deployment="claude-3-7-`<br>`sonnet"`<br>`3, deployment="claude-3-5-`<br>`haiku"`<br>`4, deployment="claude-3-5-`<br>`sonnet-v2"`|
|`Open-Source`<br>`Deployable`<br>`Models`|`Meta Llama (Llama 3)`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5688/`|`Llama3.1_JEDAI_MODEL_CHAT_2`<br>`Llama3.3_JEDAI_MODEL_CHAT_2`|
|`Open-Source`<br>`Deployable`<br>`Models`|`Nvidia Nemotron`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5668/`|`nvidia/llama-3_3-nemotron-`<br>`super-49b-v1_5(Next release)`|
|`Open-Source`<br>`Deployable`<br>`Models`|`Alibaba Qwen Series`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5668/`|`Qwen3-32B(Next release)`|
|`Open-Source`<br>`Deployable`<br>`Models`|`DeepSeek Series`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5668/`|`deepseek-v3.1(`**`not support`**<br>**`tool calling`**`):`<br>`project: gcp-cdns-llm-test`<br>`location: us-west2`<br>`deployment: deepseek-`<br>`ai/deepseek-v3.1-maas`<br>`deepseek-r1:`<br>`project: gcp-cdns-llm-test`|



https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 5/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence






```
Tool calling capability
(stream/non-stream)

```


**S**






|Deployment|Non-<br>stream|
|---|---|
|`openai/gpt-oss-120b-`<br>`maas`|yes|
|`openai/gpt-oss-120b-`<br>`maas`|yes|








|Deployment|Non-stream|Stream|
|---|---|---|
|`gpt-4o`|yes|yes|
|`o4-mini`|no|no|
|`gpt-5`|yes|yes|
|`gpt-5-mini`|no|no|
|`gpt-5-2`|yes|yes|









**S**












|Deployment|Non-<br>stream|
|---|---|
|`amazon.titan-text-express-`<br>`v1`|no|
|`amazon.titan-text-lite-v1`|no|
|`anthropic.`**`claude-3-haiku`**`-`<br>`20240307-v1:0`|yes|
|`anthropic.`**`claude-3-opus`**`-`<br>`20240229-v1:0`|yes|
|` anthropic.`**`claude-3-5-`**<br>**`haiku`**`-20241022-v1:0`|yes|
|`anthropic.`**`claude-3-5-`**<br>**`sonnet`**`-20241022-v2:0`|yes|
|`us.anthropic.claude-`<br>`sonnet-4-20250514-v1:0`|yes|
|`us.anthropic.claude-3-7-`<br>`sonnet-20250219-v1:0`|yes|
|`us.anthropic.claude-opus-`<br>`4-20250514-v1:0`|yes|
|`us.anthropic.claude-opus-`<br>`4-1-20250805-v1:0`|yes|


|Category|Model Name|JedAI Instance|Configuring JedAI Web<br>Copilot:<br>Copilot → Chat Bbx → Copilot<br>Config|
|---|---|---|---|
||||`location: us-central1`<br>`deployment: deepseek-`<br>`ai/deepseek-r1-0528-maas`|
||`gpt-oss-120b`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5668/`|`gpt-oss-*:`<br>`project: gcp-cdns-llm-test`<br>`location: us-central1`<br>`deployment: openai/gpt-oss-`<br>`120b-maas`<br>`1, deployment: openai/gpt-`<br>`oss-120b-maas`<br>`2, deployment: openai/gpt-`<br>`oss-20b-maas`|
|`Proprietary`<br>`Commercial`<br>`Models`|`OpenAI GPT-5 / GPT-4o`<br>`/ GPT-4 / GPT-3.5 /`<br>`O3 / O4`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5668/`|`#thru Azure`|
|`Proprietary`<br>`Commercial`<br>`Models`|`Microsoft Azure`<br>`Openai`|`http://sjf-dsgdspr-`<br>`084.cadence.com:5668/`|`endpoint:https://llmtest01-`<br>`eastus2.openai.azure.com`<br>`api_version: 2025-01-01-`<br>`preview`<br>`deployment: gpt4o`<br>`1, deployment: o4-mini(`**`not`**<br>**`support tool calling`**`)`<br>`2, deployment: gpt-5`<br>`3, deployment: gpt-5-mini(`**`not`**<br>**`support tool calling`**`)`<br>`4, deployment: gpt-5-2`|
|`Proprietary`<br>`Commercial`<br>`Models`|`AWS Series`|`http://sjf-`<br>`dsgdspr=084.cadence.com:5668/`|`service name: bedrock-runtime`<br>`location: us-west-2`<br>`1, deployment: amazon.titan-`<br>`text-express-v1(`**`not support`**<br>**`tool calling`**`)`<br>`2, deployment: amazon.titan-`<br>`text-lite-v1(`**`not support tool`**<br>**`calling`**`)`<br>`3,`<br>`deployment: anthropic.`**`claude-`**<br>**`3-haiku`**`-20240307-v1:0`<br>`4,`<br>`deployment: anthropic.`**`claude-`**<br>**`3-opus`**`-20240229-v1:0`<br>`5,`<br>`deployment: anthropic.`**`claude-`**<br>**`3-5-haiku`**`-20241022-v1:0`<br>`6,`<br>`deployment: anthropic.`**`claude-`**<br>**`3-5-sonnet`**`-20241022-v2:0`<br>`7, deployment:`<br>`us.anthropic.claude-3-7-`<br>`sonnet-20250219-v1:0`<br>`8, deployment:`<br>`us.anthropic.claude-sonnet-4-`<br>`20250514-v1:0`<br>`9, deployment:`<br>`us.anthropic.claude-opus-4-`|



https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 6/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence



|Category|Model Name|JedAI Instance|Configuring JedAI Web<br>Copilot:<br>Copilot → Chat Bbx → Copilot<br>Config|
|---|---|---|---|
||||`20250514-v1:0`<br>`10, deployment:`<br>`us.anthropic.claude-opus-4-1-`<br>`20250805-v1:0`|


**MOCK TOOLS CALLING WORKFLOW (openai_format = True)**
**1, Define tools**


tools = [{'type': 'function',
'function': {'name': 'get_current_weather',
'description': "Get weather 。 e.g. ， What's the weather in Shanghai ？ ",
'parameters': {'type': 'object',
'required': ['location'],
'properties': {'location': {'type': 'string',
'description': "City name ， 'Beijing', 'London' "}}}}}]


**2, Define tools function**


def get_current_weather(location: str, unit: str = "celsius"):
"""
:param location: Beijing
:param unit: degree ， "celsius" or "fahrenheit"
:return: dict
"""
if "Beijing" in location:
return {"temperature": 25, "unit": unit, "description": "Sunny"}
elif "London" in location:
return {"temperature": 15, "unit": unit, "description": "Cloudy"}
else:
return {"temperature": "Unknown", "unit": unit, "description": "Unknown"}


def handle_weather_tool(tool_call):
"""
get current weather
"""
input_params =json.loads(tool_call['function']['arguments'])
location = input_params.get('location', '')
unit = input_params.get('unit', 'celsius')
results = get_current_weather(location, unit)
return f"{results}"


**3, Mock tools calling workflow**


import json
def run_model_with_tools(jedai_api_url, headers, user_message):
"""
requests.post
"""


# Initial Tool call
messages = [
{
"role": "user",
"content": user_message
}
]

while True:
request_data = {
"messages":messages,
"model": "GEMINI", # change here
"deployment": "gemini-2.5-pro", # change here
"max_tokens": 10000,
"tools": tools
}

response = requests.post(
jedai_api_url,
headers=headers,
json=request_data
)

if response.status_code != 200:
print(f"API Failed: {response.status_code}")
print(response.text)
break

response_data = response.json()


choices = response_data.get('choices', [])
if not choices:
print("No choices in response")
break

message = choices[0].get('message', {})
tool_calls = message.get('tool_calls', [])


if not tool_calls:
print("Model response:")


```
Tool calling capability
(stream/non-stream)

```


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 7/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


content = message.get('content', '')
if content:
print(content)
break


messages.append({
"role": "assistant",
"content": message.get('content', ''),
"tool_calls": tool_calls
})

for tool_call in tool_calls:
function_name = tool_call['function']['name']
arguments = json.loads(tool_call['function']['arguments'])


if function_name == "str_replace_based_edit_tool":
result = handle_editor_tool(tool_call)
elif function_name == "get_current_weather":
result = handle_weather_tool(tool_call)
else:
result = f"Unknown tool: {function_name}"

messages.append({
"role": "tool",
"tool_call_id": tool_call['id'],
"content": result
})
print(f"execute {len(tool_calls)} tools ... continue...")


**4, Calling**


user_input = "What's the weather in Beijing?"
headers={"accept": "*/*", "Content-Type": "application/json", "Authorization": f"Bearer {token}"}
run_model_with_tools(jedai_api_url, headers, user_input)


**Key Advantages**


**Unified Interface** : Single API format across all supported models
**Enhanced Security** : Centralized key management
**Future-Proof** : Access to latest model releases
**Tool Ecosystem** : Integration with both Continue's built-in tools and MCP server tools (Cadence's proprietary JedAI-AAI tools)


This framework restructuring represents a significant investment in JedAI's agent capabilities, positioning us to support sophisticated AI workflows while maintaining security and usability
standards.


***Last updated: August 28, 2025***


Notes


****1. Note: Our tool calling functionality is currently under active development.****


This wiki page will be continuously updated as we enhance and expand our tool calling capabilities. Please check back regularly for the latest information on:


 - New tool integrations

 - API improvements

 - Usage examples and best practices

 - Known limitations and workarounds


We appreciate your patience as we work to deliver a robust and comprehensive tool calling experience.


****2. Note** ： **attached config.yaml for vscode continue ****


# JedAI Mozart continue Configuration


name: Local Assistant
version: 1.0.0
schema: v1


models:

 - name: gemini-2.5-pro
model: openai
provider: openai
requestOptions:
extraBodyProperties:
model: GCP_gemini-2.5-pro
[apiBase: https://sjf-dsgdspr-084.cadence.com:2513/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey: your jedai_api_key
role:
  - chat
  - edit
  - apply


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 8/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


capabilities:
  - tool_use
 - name: Llama
model: on_prem_Llama3.3_JEDAI_MODEL_CHAT_2
provider: openai
[apiBase: https://sjf-dsgdspr-084.cadence.com:2513/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey: your jedai_api_key
roles:
  - chat
  - edit
  - apply
capabilities:
  - tool_use
 - name: DeepSeek
provider: openai
model: GCP_deepseek-ai/deepseek-r1-0528-maas
[apiBase: https://sjf-dsgdspr-084.cadence.com:2513/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey:your jedai_api_key
roles:
  - chat
  - edit
  - apply
capabilities:
  - tool_use
 - name: claude-sonnet-4-5
provider: openai
model: openai
requestOptions:
extraBodyProperties:
model: GCP_claude-sonnet-4-5
[apiBase: https://sjf-dsgdspr-084.cadence.com:2513/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey: your jedai_api_key
role:
  - chat
  - edit
  - apply
capabilities:
  - tool_use
mcpServers:

 - name: jedai-aai
type: sse
[url: http://vlsj-mozart-poc4:9500/api/aai/sse](http://vlsj-mozart-poc4:9500/api/aai/sse)
requestOptions:
headers:
Authorization: Bearer <MCP_server_api_key>
model: jedai-aai
allow_automatic_tool_calls: true
max_Steps: 15
context:

 - provider: code
 - provider: docs
  - provider: diff
 - provider: terminal
 - provider: problems
 - provider: folder
 - provider: codebase


from 2513 you can config it like below example:


name: Local Assistant
version: 1.0.0
schema: v1


models:

 - name: gemini-2.5-pro
model: openai
provider: openai
requestOptions:
extraBodyProperties:
model: GEMINI
deployment: gemini-2.5-pro
project: gcp-cdns-llm-test
location: us-central1
[apiBase: http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey: your jedai_api_key
role:
  - chat
  - edit
  - apply
capabilities:
  - tool_use
 - name: Llama
model: Llama3.3_JEDAI_MODEL_CHAT_2
provider: openai
[apiBase: http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey: your jedai_api_key
roles:
  - chat
  - edit
  - apply
capabilities:
  - tool_use


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 9/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


 - name: DeepSeek
provider: openai
model: gcp_oss
requestOptions:
extraBodyProperties:
deployment: deepseek-ai/deepseek-r1-0528-maas
project: gcp-cdns-llm-test
location: us-central1
[apiBase: http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey:your jedai_api_key
roles:
  - chat
  - edit
  - apply
capabilities:
  - tool_use
 - name: claude-sonnet-4
provider: openai
model: openai
requestOptions:
extraBodyProperties:
model: Claude
deployment: claude-sonnet-4
project: gcp-cdns-llm-test
location: us-east5
anthropic_version: vertex-2023-10-16
[apiBase: http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)
apiKey: your jedai_api_key
role:
  - chat
  - edit
  - apply
capabilities:
  - tool_use
mcpServers:

 - name: jedai-aai
type: sse
[url: http://vlsj-mozart-poc4:9500/api/aai/sse](http://vlsj-mozart-poc4:9500/api/aai/sse)
requestOptions:
headers:
Authorization: Bearer <MCP_server_api_key>
model: jedai-aai
allow_automatic_tool_calls: true
max_Steps: 15
context:

 - provider: code
 - provider: docs
  - provider: diff
 - provider: terminal
 - provider: problems
 - provider: folder
 - provider: codebase


3 Comments


[Srinivas Gudla](https://wiki.cadence.com/confluence/display/~sgudla)


Oct 13, 2025


How do I get MCP_server_api_key?


[Leilei Yu](https://wiki.cadence.com/confluence/display/~llyu)


Oct 23, 2025



No labels



Thanks Zhe, this page is really useful! I'm wondering when the LLM model determines a function calling should be used(i.e. it should return 'tool_calls' instead of 'content'), it looks if I
have the "tools" parameter, then this feature will be enabled, right?


Thanks,


Leilei


[Albert Azali](https://wiki.cadence.com/confluence/display/~alberta)


Dec 10, 2025


Hi, what is the endpoint for Agent tooling/function? I tried [http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm but this give me https error.](http://sjf-dsgdspr-084.cadence.com:5668/api/copilot/v1/llm)


Thanks

...


[requests.exceptions.SSLError: HTTPSConnectionPool(host='sjf-dsgdspr-084.cadence.com', port=5668): Max retries exceeded with url: /api/copilot/v1/llm (Caused by](http://sjf-dsgdspr-084.cadence.com/)
SSLError(SSLError(1, '[SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:997)')))


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 10/11


1/16/26, 5:46 PM JedAI Agent Tooling & Function Calling - JEDAI - Confluence


https://wiki.cadence.com/confluence/spaces/JEDAI/pages/978018914/JedAI+Agent+Tooling+Function+Calling 11/11


