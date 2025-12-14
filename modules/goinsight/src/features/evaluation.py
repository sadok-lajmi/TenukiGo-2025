from typing import List

from .constants import MOVE_CLASSIFICATION_BOUNDS
from .analysis import Analizer

class Evaluator:
    """
    Used to classify the quality of plays.

    :param analizer: Analyzer used to analyze the game.
    :type analizer: Analizer
    """
    def __init__(self, analizer: Analizer):
        self.analizer = analizer

    def classify_move(self, turn: int) -> str:
        """
        Classify the move in one of the following categories.

        - BEST
        - EXCELLENT
        - GOOD
        - INACCURACY
        - MISTAKE
        - BLUNDER

        :param turn: Turn of the move classified.
        :type turn: int
        :return: Classification ("BEST"/"EXCELLENT"/...).
        :rtype: str
        :raises ValueError: If this is called before the analysis of the game.
        :raises ValueError: If the value of turn is invalid.
        :raises ValueError: If the winrate loss of the turn is invalid.
        """
        game_analysis = self.analizer.game_analysis
        if game_analysis is None:
            raise ValueError(f"Evaluator.classify_move(turn) -- Please run the game analysis before this method.")
        
        game_length = len(game_analysis)
        if turn >= game_length:
            raise ValueError(f"Evaluator.classify_move(turn) -- The value of turn is invalid for a game with {game_length} turns: {turn}")
        
        if turn == 0:
            return "BEST"
        
        player = game_analysis[turn]["rootInfo"]["currentPlayer"]
        turn_winrate = game_analysis[turn]["rootInfo"]["winrate"]
        previous_turn_winrate = game_analysis[turn - 1]["rootInfo"]["winrate"]

        winrate_loss = previous_turn_winrate - turn_winrate

        if player == "W":
            winrate_loss = - winrate_loss

        for classification in MOVE_CLASSIFICATION_BOUNDS.keys():
            low, high = MOVE_CLASSIFICATION_BOUNDS[classification]
            if low <= winrate_loss <= high:
                return classification

        raise ValueError(f"Evaluator.classify_move(turn) -- Invalid winrate loss for turn {turn}: {winrate_loss} (must be between -1.0 and 1.0)")
    
    def classify_game(self) -> List[str]:
        """
        Classify all moves of the game in one of the following categories.

        - BEST
        - EXCELLENT
        - GOOD
        - INACCURACY
        - MISTAKE
        - BLUNDER

        :return: List of classifications (e.g.: ["BEST", "EXCELLENT", ...]).
        :rtype: List[str]
        :raises ValueError: If this is called before the analysis of the game.
        :raises ValueError: If the winrate loss of the turn is invalid.
        """
        return [self.classify_move(turn) for turn in range(len(self.analizer.game_analysis))]

if __name__ == "__main__":
    analizer = Analizer("games/sapindenoel_tronque.sgf")
    evaluator = Evaluator(analizer)
    analizer.shalow_game_analysis()
    list_score_lead = analizer.game_score_lead()
    list_classifications = evaluator.classify_game()

    print("turn | scoreLead | classification")
    for i, score_lead in enumerate(list_score_lead):
        if i < 10:
            print(f"{i}    | {score_lead} | {list_classifications[i]}")
        elif i < 100:
            print(f"{i}   | {score_lead} | {list_classifications[i]}")
        else:
            print(f"{i}  | {score_lead} | {list_classifications[i]}")
