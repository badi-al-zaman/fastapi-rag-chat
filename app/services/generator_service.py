from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
from llama_index.core.tools import FunctionTool

from typing import List, Dict

from app.models import conversation_crud
from app.models import conversation_models
from app.utils.logger import logger
from app.services.retriever_service import search_query_pipline
from typing import Annotated

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

Settings.llm = Ollama(
    model="llama3.1:8b",  # local model name
    request_timeout=360.0,
    context_window=8000
)


# dp_model = Ollama(
#     model="deepseek-r1:8b",  # local model name
#     request_timeout=360.0,
#     thinking=True,
#     # Manually set the context window to limit memory usage
#     context_window=8000,
# )


# ========================================
# SECTION 5: CONTEXT AUGMENTATION
# ========================================

def augment_prompt_with_context(query: str, search_results: List[Dict]) -> str:
    """
    Build augmented prompt with retrieved context for LLM.

    This section demonstrates:
    - Context assembly from search results
    - Prompt construction
    - Information formatting
    - Context length management
    """
    # Assemble context from search results
    context_parts = []
    for i, result in enumerate(search_results, 1):
        if "similarity" in result:  # coming from rag pipeline
            context_parts.append(
                f"Source {i}: {result['metadata']['title']}\n{result['content']}"
            )
        elif "score" in result:  # coming from DB to build chat history
            context_parts.append(
                f"Source {i}: {result['metadata']['title']}\n{result['content']}"
            )

    context = "\n\n".join(context_parts)

    # Build augmented prompt
    augmented_prompt = f"""
Based on the following resources, answer the user question.

resources:
{context}

QUESTION: {query}

Please provide a clear, accurate answer based on the resources above.
If the information is not available in the resources, say so.
Include relevant resources details and any limitations or requirements.
"""
    return augmented_prompt


# ========================================
# SECTION 6: RESPONSE GENERATION
# ========================================


def generate_response(augmented_prompt: str):
    """
    Generate response using LLM

    This section demonstrates:
    - Response formatting
    - Answer synthesis
    - Output structure
    """
    model = Ollama(
        model="llama3.1:8b",  # local model name
        request_timeout=360.0,
        # Manually set the context window to limit memory usage
        context_window=8000,
    )

    # LLM processing...
    response = model.chat(messages=[ChatMessage(
        role="user", content=augmented_prompt)
    ])
    return response


def search_documents_v1(query: Annotated[
    str, "The search query used to find relevant text segments"
]) -> List[dict]:
    """Search through articles related to John Adams and James Monroe.

    Args:
    query (str): The search query used to find relevant information within
        the set of articles.

    Returns:
    list[dict]: A list of dictionaries, where each dictionary represents a
        relevant document segment with the following fields:
            - id (str): A unique identifier corresponding to the document name.
            - content (str): The main text content of the document, used to
              generate or support an answer to the user's query.
            - title (str): The title of the Wikipedia article from which
              the content was retrieved.
    Example:
    >> search_documents_v1("foreign policy")
    [
        {
            "id": "john_adams_policies",
            "content": "Adams maintained peace with France despite strong opposition...",
            "title": "Foreign Policy of John Adams"
        },
        ...
    ]
    """
    if query.strip() != "":
        search_results = search_query_pipline(query)
        return search_results
    return []


system_prompt_v1 = """
You are an intelligent research assistant specializing in topics related to John Adams and James Monroe.
Your goal is to accurately answer user questions.
---
### Capabilities & Decision Rules:
- use your internal knowledge for general or broad questions.
- For specific, factual, or historical details about John Adams or James Monroe, retrieve information from
document search tool (`search_documents_v1(query)`).
- synthesize search results clearly, avoiding unnecessary repetition of source text.
---
### Answer Format
1. **Direct Answer:** Provide a concise, clear, and well-structured response first.  
2. **Explanation / Summary of Findings (optional):**  
   Briefly summarize supporting evidence or reasoning, especially when the answer is derived from search results.
3. **Citation (when possible):** Mentions the relevant document or context, e.g., "According to [document
id]..."
"""

system_prompt = """
You are an intelligent assistant.
Your main goal is accurately answer user questions and decide if you need to call a specific tool based on the RULES FOR USE.

### Your Tools
- You can call the `search_documents(query)` function to look up information from a collection of articles about John Adams and James Monroe.

### RULES FOR TOOLS USE (critical):
- Call `search_documents` ONLY if:
    (a) the user is asking for factual / historical / specific information
    AND
    (b) that information is directly about John Adams or James Monroe
    
- Use your internal knowledge for general or broad questions like:
    • Greetings
    • Chit-chat
    • Generic knowledge...
    
### Output Format
- Provide a direct answer first.
- Optionally, follow with a short “Explanation” or “Summary of findings” section.
"""

simple_system_prompt = """
You are an intelligent research assistant powered with a document search tool to lookup for related text segments of specific topics that help you answer user questions accurately.
The tool name is `search_documents(query)` and the topics domain are:
1. John Adams.
2. James Monroe.

Your goal is to decide if `search_documents` tool is needed based on the following rules: 
    - Use `search_documents` only if the question related to the above mentioned articles. (ex: who is John Adams?, ...)
    - Do not use `search_documents` If the question is general or broad as: Greetings, Chit-chat,...ect. Instead answer directly.
    
## Output Format:
- Provide a direct answer first.
- Optionally, follow with a short “Explanation” or “Summary of findings” section.

## Expected Behavior:
→ NOT call the tool unless the user's question related to one of the above mentioned topics.
**example 1:**
-> user ask: Did John Adams represent the Continental Congress in Europe?
-> expected behavior is to call search document first because the question related to one of the above mentioned topics.
**example 2:**
-> user ask: Hello, are you ready to help me? 
-> expected behavior is to answer this question directly without calling the search tool.
"""

thinking_system_prompt = """
SYSTEM:
You are an intelligent research assistant.

You have 1 tool:
search_documents(query)

SCOPE OF TOOL:
search_documents contains documents ONLY about:
- Topic A = John Adams
- Topic B = James Monroe

RULES FOR TOOL USE (critical):
- Call search_documents ONLY if:
    (a) the user is asking for factual / historical / specific information
    AND
    (b) that information is directly about Topic A or Topic B

- DO NOT call search_documents for:
    • greetings
    • chit-chat
    • generic knowledge
    • anything not specifically and directly about Topic A or Topic B

DEFAULT:
→ do NOT call the tool unless both conditions (a) AND (b) are satisfied

OUTPUT FORMAT:
ReAct hint:
At the end of each turn you must decide:
“tool”  OR  “no tool”
Default = “no tool”.
"""


async def ask_agent_v1(session: conversation_models.SessionPublic, db):
    messages = []
    for message in session.messages:
        current_message = ChatMessage(
            **message.data
        )
        messages.append(current_message)

    model = Ollama(
        model="qwen3:8b",  # local model name qwen3:8b
        request_timeout=360.0,
        # Manually set the context window to limit memory usage
        context_window=8000,
        thinking=True
    )

    tool = FunctionTool.from_defaults(fn=search_documents_v1)

    # Call llm with initial tools + chat history + system_prompt
    response = await model.achat_with_tools(tools=[tool], chat_history=messages,
                                            system_prompt=simple_system_prompt)

    # Parse tool calls from response
    tool_calls = model.get_tool_calls_from_response(
        response, error_on_no_tool_call=False
    )

    # check if the tool call needed
    if not tool_calls:
        return response
    else:
        while tool_calls:
            # Add the LLM's response (tool call message) to the chat history
            # print("response", response.model_dump())
            # print("response.message", response.message.model_dump())

            # Store agent response
            message = conversation_crud.add_message(db, session.session_id, data=response.message.model_dump(),
                                                    tokens=None,
                                                    )
            messages.append(ChatMessage(
                **message.data
            ))

            for tool_call in tool_calls:
                tool_name = tool_call.tool_name
                tool_kwargs = tool_call.tool_kwargs

                logger.info(f"Calling {tool_name} with {tool_kwargs}")
                search_results = tool.call(**tool_kwargs).raw_output
                texts = []
                for result in search_results:
                    texts.append(
                        {"id": result["id"], "content": result["content"], "title": result["metadata"]["title"]})

                tool_md = conversation_models.MessageData(
                    role="tool",
                    additional_kwargs={"tool_call_id": tool_call.tool_id},
                    blocks=[{"block_type": "text", "text": str(texts)}],
                )

                # Store Tool response
                message = conversation_crud.add_message(db, session.session_id, data=tool_md.model_dump(),
                                                        tokens=None,
                                                        )
                messages.append(ChatMessage(
                    **message.data
                ))

                # check if the LLM can write a final response or calls more tools
                response = await model.achat_with_tools([tool], chat_history=messages,
                                                        system_prompt=simple_system_prompt)
                tool_calls = model.get_tool_calls_from_response(
                    response, error_on_no_tool_call=False
                )
        return response
        # resp.message.content

    # response = await model.achat(messages=messages, tools=[], system_prompt=system_prompt)
    # return response
    # messages.append(response.message)
    # if response.message.additional_kwargs["tool_calls"]:
    #     # only recommended for models which only return a single tool call
    #     call = response.message.additional_kwargs["tool_calls"][0]
    #     result, search_results = search_documents_v1(**call.function.arguments)
    #
    #     # add the tool result to the messages
    #     messages.append(ChatMessage(
    #         role="tool", blocks=result.message.blocks, additional_kwargs={"tool_call_id": call.function.name})
    #     )
    #     conversation_crud.add_message(db, session["session_id"], data={"role": "tool", "additional_kwargs": {
    #         "tool_call_id": call.function.name},
    #                                                                    "blocks": result.message.model_dump()["blocks"]},
    #                                   tokens=None, extra=None)
    #     final_response = await model.achat_with_tools([search_documents_v1], chat_history=messages,
    #                                                   system_prompt=system_prompt)
    # print(final_response.message.content)
    # return final_response, search_results
