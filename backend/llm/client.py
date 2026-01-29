def call_llm(prompt: str) -> dict:
    """
    返回结构化结果：
    {
        "speech": "...",
        "vote": "player_id",
        "action": {
            "vote": "player_id | null",
            "kill": "player_id | null",
            "check": "player_id | null"
        }
    }
    """
    # Default to mock implementation to keep runtime functional.
    from llm.mock import call_llm as mock_call_llm
    return mock_call_llm(prompt)