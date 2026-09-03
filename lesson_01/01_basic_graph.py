from typing import TypedDict
from langgraph.graph import StateGraph,START,END

class State(TypedDict):             #We're defining the shape of our LangGraph state.
    number:int                      #Our state will contain a number, and that number will be an integer

def add_number(state: State):
    return{
        "number":state["number"]+10
    }

def add_ten(state:State):
    return{
        "number":state["number"]+10
    }

def double_number(state:State):
    return{
        "number":state["number"]*2
    }

def route_number(state:State):           #router node
    if(state["number"]>10):
        return "double"
        
    return "add_ten"


graph=StateGraph(State)
graph.add_node("add",add_number)   #Inside my graph, create a node called add, and when that node runs, execute the add_number function
graph.add_node("double",double_number)
graph.add_node("add_ten",add_ten)

graph.add_conditional_edges(START,route_number,{"double":"double","add_ten":"add_ten"})
graph.add_edge("add_ten",END)
graph.add_edge("double",END)
app=graph.compile()

result=app.invoke({
    "number":15
})
print(result)