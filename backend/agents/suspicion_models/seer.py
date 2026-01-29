from agents.suspicion_models.base import BaseSuspicionModel

class SeerSuspicionModel(BaseSuspicionModel):

    def on_speech(self, observer, speaker_id, content):
        # Speech contradicts known role -> suspicious.
        if speaker_id in observer.memory.confirmed_roles:
            role = observer.memory.confirmed_roles[speaker_id]
            if role == "WEREWOLF" and "I am a good guy" in content:
                observer.memory.suspicion.add(speaker_id, +1.0)

    def on_vote(self, observer, voter_id, target_id):
        # Not voting confirmed wolf -> suspicious.
        for pid, role in observer.memory.confirmed_roles.items():
            if role == "WEREWOLF" and target_id != pid:
                observer.memory.suspicion.add(voter_id, +0.5)