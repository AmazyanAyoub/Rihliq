import logging
from dotenv import load_dotenv


from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from models.schemas import AgentState

from nodes.nodes import chat_node, extractor_node, flight_search_node, hotel_search_node
from setup.router import router

load_dotenv()
logger = logging.getLogger(__name__)


# ─── GRAPH ────────────────────────────────────────────────────────────────────

def create_travel_graph():
    g = StateGraph(AgentState)

    g.add_node("extractor", extractor_node)
    g.add_node("chat", chat_node)
    g.add_node("flight_search", flight_search_node)
    g.add_node("hotel_search", hotel_search_node)

    g.set_entry_point("extractor")

    g.add_conditional_edges(
        "extractor",
        router,
        {
            "chat": "chat",
            "flight_search": "flight_search",
            "hotel_search": "hotel_search",
        },
    )

    g.add_edge("flight_search", "chat")
    g.add_edge("hotel_search", "chat")
    g.add_edge("chat", END)

    return g.compile(checkpointer=MemorySaver())

async def stream(self, message: str, trip_context: dict = None, history: list = None):
    config = {"configurable": {"thread_id": trip_context.get("thread_id", "default") if trip_context else "default"}}
    
    async for chunk in self.graph.astream(
        {"messages": [HumanMessage(content=message)]},
        config=config,
        stream_mode="values",
    ):
        # Extract the last AI message token
        msgs = chunk.get("messages", [])
        if msgs:
            last = msgs[-1]
            if hasattr(last, "content") and isinstance(last.content, str):
                yield last.content

# ─── INTERFACE ────────────────────────────────────────────────────────────────

class TravelAssistant:
    def __init__(self):
        self.graph = create_travel_graph()

    async def process_message(self, user_msg: str, thread_id: str) -> AgentState:
        config = {"configurable": {"thread_id": thread_id}}
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=user_msg)]},
            config=config,
        )
        return result if isinstance(result, AgentState) else AgentState(**result)


travel_assistant = TravelAssistant()