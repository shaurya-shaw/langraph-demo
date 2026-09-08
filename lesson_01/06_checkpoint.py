#a graph that remembers a user's conversation across separate invoke() calls.

from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.tools import tool
from langchain_core.messages import BaseMessage,ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import random

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    count: int

def increament_count(state:State):
    return{
        "count":state["count"]+1
    }

graph=StateGraph(State)

graph.add_node("increament_count",increament_count)

graph.add_edge(START,"increament_count")
graph.add_edge("increament_count",END)

memory=MemorySaver()
app=graph.compile(checkpointer=memory)

config={
    "configurable":{
        "thread_id":"user-1"
    }
}

result=app.invoke(
    {
        "messages":[
            {
                "role":"user",
                "content":"Hello"
            }
        ],
        "count":0
    },
    config
)

result=app.invoke(
    {
        "messages":[
            {
                "role":"user",
                "content":"How are you?"
            }
        ]
    },
    config
)

print(result["messages"])
print(result["count"])