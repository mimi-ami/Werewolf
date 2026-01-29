WEREWOLF_NIGHT_DISCUSSION_PROMPT = """
It is night. You are discussing with other werewolves in secret.

Rules:
- Only werewolves can see this info.
- Coordinate to choose a kill target.
- You do not have to fully agree, but only one target will be chosen.

Known:
- Werewolf team: {wolves}
- Previous night discussion: {night_summary}
- Alive players: {alive_players}

Your task:
1. State your preferred target and why.
2. Respond to teammates' ideas.
3. Propose your final target.
"""

def build_wolf_night_prompt(wolves, night_summary, alive_players):
    return WEREWOLF_NIGHT_DISCUSSION_PROMPT.format(
        wolves=wolves,
        night_summary=night_summary,
        alive_players=alive_players,
    )