from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage,ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import random

class State(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]
    retries:int

#ToolNode itself doesn't conveniently update your custom retries field just because a tool failed.
def increament_retries(state:State):
    return{
        "retries":state["retries"]+1
    }

def check_retries(state:State):
    if state["retries"]<3:
        return "retry"

    return "stop"

@tool
def risky_calculator(a:int,b:int)->int:
    """multiply two number,but occassionally fail"""
    if random.random() < 0.6:
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

def check_tools_result(state:State):
    last_message=state["messages"][-1]

    """
    isinstance(object, type)
    It asks:
    Is this object an instance of this type?
    x = 10
    isinstance(x, int)
    Your last messages list can contain different types:
    HumanMessage
    AIMessage
    ToolMessage
    AIMessage
    """
    if isinstance(last_message,ToolMessage):   
        if last_message.status=="error":
            return "error"

    return "success"


tool_node=ToolNode(tools,handle_tool_errors=True)  

graph=StateGraph(State)

graph.add_node("llm",call_llm)
graph.add_node("tools",tool_node)
graph.add_node("retry_counter",increament_retries)

graph.add_edge(START,"llm")
graph.add_conditional_edges("llm",should_continue,{"tools":"tools","end":END})
graph.add_conditional_edges("tools",check_tools_result,{"error":"retry_counter","success":"llm"})
graph.add_conditional_edges("retry_counter",check_retries,{"retry":"tools","stop":END})

app=graph.compile()

result=app.invoke({
    "messages":[{
        "role":"user",
        "content":"What is 30*5?"
    }],
    "retries":0
})

for message in result["messages"]:
    print(message)

print("Retries:",result["retries"])


