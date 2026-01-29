from llm.client import call_llm
from agents.prompts.review import build_review_prompt

def run_agent_review(agent, final_result):
    context = {
        "role": agent.role.name,
        "final_result": final_result,
        "final_suspicions": agent.memory.suspicion.scores,
        "confirmed_roles": agent.memory.confirmed_roles,
        "vote_history": agent.vote_history,
        "key_events": agent.memory.events[-10:],
    }

    prompt = build_review_prompt(context)
    review = call_llm(prompt)
    return review
