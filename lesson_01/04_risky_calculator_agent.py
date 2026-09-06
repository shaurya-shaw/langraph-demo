from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import random

class State(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]
    tool_error:str
    retries:int

def risky_calculator(a:int,b:int)->int:
    """multiply two number,but occassionally fail"""
    if random.random() < 0.7:
        raise RuntimeError("calculator temporarily failed")

    return a*b

tools=[risky_calculator]
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
        "content":"What is 30*5?"
    }]
})

for message in result["messages"]:
    print(message)
