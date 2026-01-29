from agents.suspicion_models.base import BaseSuspicionModel

class WerewolfSuspicionModel(BaseSuspicionModel):

    def on_speech(self, observer, speaker_id, content):
        # Being attacked -> retaliate.
        if observer.player_id in content:
            observer.memory.suspicion.add(speaker_id, +0.5)

    def on_vote(self, observer, voter_id, target_id):
        # Voting a true wolf should look suspicious to others.
        if target_id in observer.wolf_team:
            observer.memory.suspicion.add(voter_id, +0.4)