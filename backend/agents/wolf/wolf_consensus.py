from collections import Counter

def reach_kill_consensus(wolf_responses):
    """
    wolf_responses:
    [
      {"wolf": "A", "kill": "P3"},
      {"wolf": "B", "kill": "P3"},
      {"wolf": "C", "kill": "P5"}
    ]
    """
    votes = [r["kill"] for r in wolf_responses if r["kill"]]
    if not votes:
        return None

    counter = Counter(votes)
    return counter.most_common(1)[0][0]
