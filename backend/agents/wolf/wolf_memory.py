class WolfSharedMemory:
    """
    所有狼人共享
    """

    def __init__(self):
        self.wolves = []              # 狼人ID列表
        self.night_logs = []          # 夜晚讨论记录
        self.suspicion_table = {}     # 对每个玩家的共同怀疑值
        self.last_kill = None

    def add_message(self, wolf_id, message):
        self.night_logs.append({
            "wolf": wolf_id,
            "message": message
        })

    def update_suspicion(self, player_id, delta):
        self.suspicion_table[player_id] = \
            self.suspicion_table.get(player_id, 0) + delta
