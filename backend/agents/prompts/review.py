REVIEW_SYSTEM_PROMPT = """
You just finished a Werewolf game.

This is a post-game review, not the game itself.
Please be calm and analytical.
Admit mistakes when appropriate.
Highlight key turning points.
You do NOT need to hide your role.
"""

def build_review_prompt(context):
    return f"""
{REVIEW_SYSTEM_PROMPT}

Your role: {context["role"]}
Final result: {context["final_result"]}

Final suspicions:
{context["final_suspicions"]}

Confirmed roles:
{context["confirmed_roles"]}

Vote history:
{context["vote_history"]}

Key events:
{context["key_events"]}

Reply in the following JSON format:

{{
  "overall_strategy": "...",
  "key_judgements": [
    {{
      "round": 2,
      "judgement": "...",
      "based_on": "...",
      "was_correct": true
    }}
  ],
  "biggest_mistake": "...",
  "turning_point": "...",
  "if_play_again": "..."
}}
"""