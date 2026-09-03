from typing import TypedDict
from langgraph.graph import StateGraph,START,END
import random

class State(TypedDict):
    number:int
    iteration:int

def generate_number(state:State):
    return{
        "number": random.randint(1, 100)
    }

def increase_number(state:State):
    return{
        "number":state["number"]+10,
        "iteration":state["iteration"]+1
    }

def check_number(state:State):
    if(state["number"]>=50):
        return "done"
    else:
        return "increase_number"

graph=StateGraph(State)

graph.add_node("generate_number",generate_number)
graph.add_node("increase_number",increase_number)

graph.add_edge(START,"generate_number")
graph.add_conditional_edges("generate_number",check_number,{"increase_number":"increase_number","done":END})
graph.add_conditional_edges("increase_number",check_number,{"increase_number":"increase_number","done":END})

app=graph.compile()
result=app.invoke({
    "iteration":0,
    "number":0
})
print(result)