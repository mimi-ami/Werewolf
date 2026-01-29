class GameReviewManager:

    def __init__(self, game, agents):
        self.game = game
        self.agents = agents

    def generate_reviews(self, final_result):
        reviews = {}
        for agent in self.agents:
            reviews[agent.player_id] = run_agent_review(
                agent, final_result
            )
        return reviews
