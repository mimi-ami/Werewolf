def on_player_speech(observer, speaker_id, content):
    """
    observer: Agent
    speaker_id: speaker id
    """
    if speaker_id == observer.player_id:
        return

    # Simple keyword heuristics.
    if "whatever" in content or "don't know" in content:
        observer.memory.suspicion.add(speaker_id, +0.2)

    if "I think" in content and "logic" in content:
        observer.memory.suspicion.add(speaker_id, -0.1)


def on_vote(observer, voter_id, target_id):
    if voter_id == observer.player_id:
        return

    # Bandwagon vote -> more suspicious.
    observer.memory.suspicion.add(voter_id, +0.1)

    # Voting someone I suspect -> slight trust.
    if observer.memory.suspicion.get(target_id) > 0.5:
        observer.memory.suspicion.add(voter_id, -0.2)


def on_seer_check(observer, target_id, result):
    if result == "WEREWOLF":
        observer.memory.suspicion.scores[target_id] = 5.0
        observer.memory.confirmed_roles[target_id] = "WEREWOLF"
    else:
        observer.memory.suspicion.scores[target_id] = -3.0


def on_player_killed(observer, dead_id):
    # If I trusted the dead, suspect those I already doubted.
    if observer.memory.suspicion.get(dead_id) < -0.5:
        for pid, score in observer.memory.suspicion.scores.items():
            if score > 0.5:
                observer.memory.suspicion.add(pid, +0.2)