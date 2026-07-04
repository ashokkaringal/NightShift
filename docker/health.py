"""NightShift container health + ADK graph verification."""

from __future__ import annotations

from fastapi import FastAPI

from agents.adk.graph import root_agent

app = FastAPI(title="NightShift Health", version="0.1.0")


@app.get("/health")
def health() -> dict[str, object]:
    sub_agents = [agent.name for agent in root_agent.sub_agents]
    return {
        "status": "ok",
        "service": "nightshift",
        "sub_agents": sub_agents,
    }
