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
    recent_speeches = None
    if isinstance(visible_speeches, list):
        recent_speeches = visible_speeches[-2:]
    else:
        recent_speeches = visible_speeches

    return f"""
{system_prompt}

{role_prompt}

[Personality]
- Aggressiveness: {personality.aggressiveness}
- Deception: {personality.deception}
- Logic: {personality.logic}
- Tone: {personality.tone}
- Quirk: {personality.quirk}

[Memory Summary]
{memory_summary}

[Visible Events]
{visible_events}

[All Prior Speeches]
{visible_speeches}

[Recent Speeches]
{recent_speeches}

[Player List]
{player_names}

[Game State]
{context}

Rules for output:
- Only mention players using ids shown in [Player List] (e.g. P1, P2).
- Only choose actions allowed by your role and the [Game State].
- If an action is unavailable, return null/false for it.
- When it is not your action phase, set all action fields to null/false.
- \u8bf7\u4f7f\u7528\u4e0e\u4e0a\u9762\u7684\u4e2a\u6027\u4e00\u81f4\u7684\u53d1\u8a00\u98ce\u683c\uff0c\u907f\u514d\u4e0e\u5176\u4ed6\u73a9\u5bb6\u7684\u53d1\u8a00\u8fc7\u4e8e\u76f8\u4f3c\u3002
- \u5982\u679c\u6709\u53ef\u7528\u7684\u4e4b\u524d\u53d1\u8a00\uff0c\u8bf7\u81f3\u5c11\u5f15\u7528\u4e00\u6761\u53d1\u8a00\u7684\u610f\u601d\uff0c\u4e0d\u8981\u53ea\u8bf4\u201c\u6211\u662f\u597d\u4eba\u201d\u8fd9\u7c7b\u6a21\u677f\u8bdd\u3002
- \u5c3d\u91cf\u4e0d\u8981\u91cd\u590d\u4e0a\u4e00\u8f6e\u7684\u89c2\u70b9\uff1b\u5982\u679c\u8981\u540c\u610f\uff0c\u8bf7\u8865\u5145\u65b0\u7406\u7531\uff0c\u5426\u5219\u8bf7\u9009\u62e9\u201c\u8df3\u8fc7\u201d\u3002
- \u53ea\u80fd\u5728 [Game State] \u7684 dead_players \u4e2d\u63d0\u53ca\u201c\u6b7b\u4ea1\u201d\u6216\u201c\u51fa\u5c40\u201d\uff1b\u4e0d\u8981\u7f16\u9020\u6b7b\u4ea1\u3002
- \u7981\u6b62\u4f7f\u7528\u5355\u5b57\u6bcd\u201cP\u201d\u6307\u4ee3\u73a9\u5bb6\uff1b\u5fc5\u987b\u5199\u5b8c\u6574\u7f16\u53f7\u5982 P1, P2, P3\u3002

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
