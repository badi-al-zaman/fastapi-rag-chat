from typing import Annotated
from app.services.embedding_service import get_index
from app.utils.logger import logger
from llama_index.llms.ollama import Ollama

from llama_index.core.agent import FunctionAgent


async def search_documents(query: Annotated[
    str, "a query used to retrieve relevant texts"
]) -> str:
    """Search through wiki articles about John Adams and James Monroe."""
    if query.strip() != "":
        logger.info(f"search using {query}")
        index = get_index()
        model = Ollama(
            model="llama3.1:8b",  # local model name
            request_timeout=360.0,
            # Manually set the context window to limit memory usage
            context_window=8000,
        )
        query_engine = index.as_query_engine(llm=model, similarity_top_k=3)
        response = await query_engine.aquery(query)
        # query_engine = wiki_index_v2.as_retriever()
        # response = await query_engine.aretrieve(query)
        # results = []
        # for doc in response:
        #     results.append(doc.text_template)
        # print(results)
        return str(response)
    return ""


# ### Response Guidelines
# 1. **Clarity & Accuracy:** Provide concise, factual, and verifiable answers based on the search results.
# 2. **Citation:** When possible, mention the source context (e.g., “According to the John Adams article…”).
# 3. **Reasoning:** If search results are unclear or conflicting, summarize what is known and note uncertainties.
# 4. **Relevance:** Only include information related to the query topic. Exclude unrelated content.
# 5. **Style:** Write in a neutral, informative tone — similar to a historical researcher explaining a finding.


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


# from llama_index.core.agent.workflow import AgentWorkflow

# Now we can ask questions about the documents
async def ask_agent_v2(query: str, chat_memory):
    # AgentWorkflow (an agent capable of managing multiple agents).
    # Create an enhanced workflow with tools
    # agent = AgentWorkflow.from_tools_or_functions(
    #     [search_documents],
    #     llm=model,
    #     system_prompt=system_prompt,
    # )

    # https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/tools#return-direct
    # tool = QueryEngineTool.from_defaults(
    #     search_documents,
    #     # name="<name>",
    #     # description="<description>",
    #     return_direct=True,
    # )
    model = Ollama(
        model="llama3.1:8b",  # local model name
        request_timeout=360.0,
        # Manually set the context window to limit memory usage
        context_window=8000,
    )
    workflow = FunctionAgent(
        tools=[search_documents],
        llm=model,
        system_prompt=simple_system_prompt,
    )
    response = await workflow.run(
        query, memory=chat_memory
    )
    return response
