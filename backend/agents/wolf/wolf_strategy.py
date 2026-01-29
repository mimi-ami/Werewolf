def choose_scapegoat(agent):
    """
    选一个：
    - 发言活跃
    - 当前怀疑值中等（容易被推）
    """
    candidates = [
        (pid, score)
        for pid, score in agent.memory.suspicion.scores.items()
        if 0.3 < score < 1.2
    ]
    if not candidates:
        return None

    return sorted(candidates, key=lambda x: x[1])[0][0]
