from agents.suspicion_models.base import BaseSuspicionModel

class VillagerSuspicionModel(BaseSuspicionModel):

    def on_speech(self, observer, speaker_id, content):
        if speaker_id == observer.player_id:
            return

        # Vague statements.
        if any(k in content for k in ["don't know", "whatever", "depends"]):
            observer.memory.suspicion.add(speaker_id, +0.3)

        # Emotional accusation.
        if "you are definitely a wolf" in content:
            observer.memory.suspicion.add(speaker_id, +0.2)

    def on_vote(self, observer, voter_id, target_id):
        # Voting the same as me -> slight trust.
        if target_id == observer.last_vote:
            observer.memory.suspicion.add(voter_id, -0.2)