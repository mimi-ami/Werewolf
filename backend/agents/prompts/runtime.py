def build_runtime_prompt(
    system_prompt,
    role_prompt,
    phase_prompt,
    memory_summary,
    visible_events,
    visible_speeches,
    player_names,
    personality,
    context,
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

[All Prior Speeches]
{visible_speeches}

[Player List]
{player_names}

[Game State]
{context}

Rules for output:
- Only mention players using ids shown in [Player List] (e.g. P1, P2).
- Only choose actions allowed by your role and the [Game State].
- If an action is unavailable, return null/false for it.
- When it is not your action phase, set all action fields to null/false.

{phase_prompt}

[Current Judgement]
Top suspects:
{top_suspects}

Confirmed roles:
{confirmed_roles}

Please respond strictly in JSON format:

{{
  \"thinking\": \"Your inner reasoning (<=200 chars)\",
  \"speech\": \"Your table talk (<=80 chars)\",
  \"action\": {{
      \"vote\": \"player_id or null\",
      \"kill\": \"player_id or null\",
      \"check\": \"player_id or null\",
      \"guard\": \"player_id or null\",
      \"save\": true or false or null,
      \"poison\": \"player_id or null\"
  }}
}}
"""
