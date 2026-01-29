def build_werewolf_speech(agent, scapegoat):
    history = agent.memory.events[-3:]

    return f"""
I noticed {scapegoat} started acting strange a few rounds ago.

Specifically:
- {history[0] if history else ""}
- Their explanation has been inconsistent.

I am not saying we must vote them out, but they deserve scrutiny.
"""