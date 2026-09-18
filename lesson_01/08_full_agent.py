from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt,Command

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage,ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import random

class State(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]
    retries:int
    approved:bool

@tool
def calculator(a:int,b:int,task:str)->float:
    """perform calculation addition,substraction,division,multiplication"""
    if task=="addition":
        return a+b
    elif task=="substraction":
        return a-b
    elif task=="division":
        if b==0:
            raise ValueError("cannot divided by zero")
        return a/b
    elif task=="multiplication":
        return a*b
    else:
        raise ValueError("Invalid task")

@tool
def search_web(query:str)->str:
    """web search"""
    return f"web searched successfull for{str}"

@tool
def send_email(recipient:str,subject:str,message:str)->str:
    """send email"""
    return f"recipient:{recipient} /n subject:{subject} /n message:{message}"

@tool
def delete_file(filename:str)->str:
    """delete filename"""
    return f"{filename} deleted"


tools=[calculator,search_web,send_email,delete_file]
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
    last_message=state["messages"][-1]

    if not last_message.tool_calls:
        return "end"
    tool_name=last_message.tool_calls[0]["name"]
    if tool_name in ["send_email","delete_file"]:
        return "approval"

    return "tools"
    
    

def request_approval(state:State):
    tool_call=state["messages"][-1].tool_calls[0]
    decision=interrupt(
        {
            "question":f"do you approve this action",
            "tool":tool_call["name"],
            "args":tool_call["args"]
        }
    )
    return{
        "approved":decision
    }

def increament_retries(state:State):
    return{
        "retries":state["retries"]+1
    }

def check_retries(state:State):
    if(state["retries"]<3):
        return "retry"
    return "stop"

def check_tool_result(state:State):
    result=state["messages"][-1]
    if isinstance(result,ToolMessage):
        if result.status=="error":
            return "error"

    return "success"

def check_approval(state:State):
    if state["approved"]:
        return "approved"
    return "rejected"

tool_node=ToolNode(tools,handle_tool_errors=True)

graph=StateGraph(State)

graph.add_node("call_llm",call_llm)
graph.add_node("request",request_approval)
graph.add_node("increament",increament_retries)
graph.add_node("tools",tool_node)

graph.add_edge(START,"call_llm")
graph.add_conditional_edges("call_llm",should_continue,{"tools":"tools","end":END,"approval":"request"})
graph.add_edge("tools","call_llm")
graph.add_conditional_edges("tools",check_tool_result,{"error":"increament","success":"call_llm"})
graph.add_conditional_edges("increament",check_retries,{"retry":"tools","stop":END})
graph.add_conditional_edges("request",check_approval,{"approved":"tools","rejected":END})

memory=MemorySaver()
app=graph.compile(checkpointer=memory)

config={
    "configurable":{
        "thread_id":"terminal-agent"
    }
}

while True:

    user_message = input("\nYou: ")

    if user_message.lower() in ["exit", "quit"]:
        break

    result = app.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "retries": 0,
            "approved": False
        },
        config
    )

    if "__interrupt__" in result:

        interrupt_data = result["__interrupt__"][0].value

        print("\n⚠️ Approval required")
        print("Tool:", interrupt_data["tool"])
        print("Arguments:", interrupt_data["args"])

        decision = input("Approve? (y/n): ").lower()

        approved = decision == "y"

        result = app.invoke(
            Command(resume=approved),
            config
        )

    if result["messages"]:
        print("\nAgent:", result["messages"][-1])