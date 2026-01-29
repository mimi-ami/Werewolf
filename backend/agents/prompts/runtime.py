def build_runtime_prompt(
    system_prompt,
    role_prompt,
    phase_prompt,
    memory_summary,
    visible_events,
    personality,
):
    top_suspects = memory_summary.get("top_suspects") if isinstance(memory_summary, dict) else None
    confirmed_roles = memory_summary.get("confirmed_roles") if isinstance(memory_summary, dict) else None

    return f"""
{system_prompt}

{role_prompt}

[Personality]
- Aggressiveness: {personality.aggressiveness}
- Deception: {personality.deception}
- Logic: {personality.logic}

[Memory Summary]
{memory_summary}

[Visible Events]
{visible_events}

{phase_prompt}

[Current Judgement]
Top suspects:
{top_suspects}

Confirmed roles:
{confirmed_roles}

Please respond strictly in JSON format:

{{
  "thinking": "Your inner reasoning (<=200 chars)",
  "speech": "Your table talk (<=80 chars)",
  "action": {{
      "vote": "player_id or null",
      "kill": "player_id or null",
      "check": "player_id or null"
  }}
}}
"""