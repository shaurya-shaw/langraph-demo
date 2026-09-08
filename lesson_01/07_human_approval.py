#Build a graph representing an agent that wants to perform a potentially dangerous action.
#by introducing human in a loop

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

class State(TypedDict):
    action: str
    approved: bool


def request_approval(state:State):
    decision=interrupt(
        {
            "question":f"do you approve:{state["action"]}"
        }
    )
    """
    At interrupt LangGraph did not execute the next line:
    Instead, it checkpointed the current state and returned the interrupt information.
    """
    return{
        "approved":decision
    }

def execute_action(state:State):
    print(f"executing {state['action']}")
    return{}

def check_approval(state:State):
    if state["approved"]:
        return "execute"

    return "end"

graph=StateGraph(State)

graph.add_node("request",request_approval)
graph.add_node("execute",execute_action)

graph.add_edge(START,"request")
graph.add_conditional_edges("request",check_approval,{"execute":"execute","end":END})

memory=MemorySaver()
app=graph.compile(checkpointer=memory)

config={
    "configurable":{
        "thread_id":"approval-1"
    }
}

result=app.invoke(
    {
        "action":"delete database",
        "approved":False
    },
    config
)


result=app.invoke(
    Command(resume=True),    #The human has responded. Continue the paused graph with this value
    config
)
print(result)




"""
interrupt()
   ↓
pause graph
   ↓
save checkpoint
   ↓
return control to application
"""