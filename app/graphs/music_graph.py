# app/graphs/music_graph.py
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.intake_agent import intake_agent
from app.agents.research_agent import research_agent
from app.agents.playlist_agent import playlist_agent
from app.agents.session_agent import session_agent


class MusicState(TypedDict, total=False):
    user_id: str
    preferences: Dict[str, Any]
    research: Dict[str, Any]
    playlist: Dict[str, Any]
    session_info: Dict[str, Any]


class MusicDiscoveryGraph:
    def __init__(self) -> None:
        graph = StateGraph(MusicState)

        # Nodes
        graph.add_node("intake", intake_agent)
        graph.add_node("research", research_agent)
        graph.add_node("playlist", playlist_agent)
        graph.add_node("session", session_agent)

        # Entry + edges
        graph.set_entry_point("intake")
        graph.add_edge("intake", "research")
        graph.add_edge("research", "playlist")
        graph.add_edge("playlist", "session")
        graph.add_edge("session", END)

        self._graph = graph.compile()

    def run(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entry point from FastAPI.

        We explicitly create the initial state so 'user_id' and 'preferences'
        are ALWAYS present for the first node (intake).
        """
        initial_state: MusicState = {
            "user_id": user_id,
            "preferences": preferences,
        }
        return self._graph.invoke(initial_state)
