class WolfChannel:
    """
    只在夜晚激活
    """

    def __init__(self, shared_memory):
        self.memory = shared_memory

    def broadcast(self, wolf_id, message):
        self.memory.add_message(wolf_id, message)

    def get_context(self):
        return self.memory.night_logs
