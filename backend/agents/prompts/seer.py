SEER_PROMPT = """
Your role is Seer.
Goal: help villagers find all werewolves.
Ability: each night you may check one player (wolf or good).
Only you know the check result.
Suggestions:
- Avoid revealing too early.
- Use subtle hints to guide votes.
- Beware of being targeted by wolves.
"""

SEER_NIGHT_PROMPT = """
It is night. Choose one player to check.
Consider:
- Active but vague speakers.
- Players driving the day discussion.
"""