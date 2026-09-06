from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

class State(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]  #add_messages tells LangGraph how to merge new messages into the existing message history rather than simply overwriting the list.
    """
    list[BaseMessage]
    This describes the type of the value.
    HumanMessage(...),
    AIMessage(...),
    ToolMessage(...),
    AIMessage(...)
    BaseMessage is the common parent type for these different message types.
    Annotated lets us attach extra information/metadata to a type.
    """

@tool
def multiply(a:int,b:int) ->int:
    """multiplying two numbers"""
    return a*b

@tool
def add(a:int,b:int) ->int:
    """add two number"""
    return a+b



#why tool why not function
#becoz function is called by the code whereas in tool the LLM can decide that the function should be called or not or call multiple times and also the LLM can decide the order of calling the tools

tools=[multiply,add]

llm=ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

llm_with_tools=llm.bind_tools(tools)

def call_llm(state:State):
    response=llm_with_tools.invoke(state["messages"])

    return{
        "messages":[response]
    }

def should_continue(state:State):
    last_message=state['messages'][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


"""
The below node knows how to:
1. Read the LLM's tool call
2. Find the corresponding Python tool
3. Execute it
4. Create a ToolMessage
5. Put that result into the message state
"""
tool_node=ToolNode(tools)   

graph=StateGraph(State)

graph.add_node("llm",call_llm)
graph.add_node("tools",tool_node)

graph.add_edge(START,"llm")
graph.add_conditional_edges("llm",should_continue,{"tools":"tools","end":END})
graph.add_edge("tools","llm")

app=graph.compile()

result=app.invoke({
    "messages":[{
        "role":"user",
        "content":"What is (20 + 30)*5?"
    }]
})

for message in result["messages"]:
    print(message)



"""
"Where did the LLM actually call calculator()?"
It didn't.
The LLM generated:
tool_calls = [
    {
        "name": "calculator",
        "args": {
            "a": 127,
            "b": 43
        }
    }
]
"""

