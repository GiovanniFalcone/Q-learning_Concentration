import json


class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self._pairs = 0
        self._last_pair_was_correct = False
        self._click_for_pair = 0

    @property
    def get_pairs(self):
        return self._pairs

    @get_pairs.setter
    def set_pairs(self, value):
        self._pairs = value

    @property
    def get_last_pair_was_correct(self):
        return self._last_pair_was_correct

    @get_last_pair_was_correct.setter
    def set_last_pair_was_correct(self, value):
        self._last_pair_was_correct = value

    @property
    def get_number_of_clicks_for_current_pair(self):
        return self._click_for_pair

    @get_number_of_clicks_for_current_pair.setter
    def set_number_of_clicks_for_current_pair(self, value):
        self._click_for_pair = value

    def play(self, suggest, card, position, game):
        """
        This function will select a card every step of episode following the suggestion provided by algorithm.
        After that, it will update player's info.

        Parameters
        ----------
        suggest: string
            The type of suggest: none, suggest_row_col, suggest_card
        card: string 
            The card suggested by the robot. Empty if the suggest is none or suggest_row_col
        position: array of int
            Coordinates of card suggested.
                - Both >= 0 if suggest is card
                - [-1, >=0] if suggest is column
                - [>=0, -1] if suggest is row
        game: Game object
            The current game.

        Returns
        -------
        clicked_card_name: String
            The name of the card that was clicked
        clicked_card_position: array of int
            Coordinates of clicked card.
        match: boolean
            true if a pair has been found, false otherwise
        """

        # get a card
        if suggest == 'none':
            # get "random" card (as the turns progress, the probability of making matches increases, so it is not entirely random) 
            clicked_card_name, clicked_card_position, _, match = game.make_move(self)
        elif suggest == 'card':
            # take the card suggested
            clicked_card_name, clicked_card_position, _, match = game.make_move_by_card(card, position)
        else:
            # take random card based on specific row or col
            row = position[0]
            column = position[1]

            number_suggested = row if column == -1 else column
            clicked_card_name, clicked_card_position, _, match = game.make_move_by_grid(suggest, number_suggested)

        # update player info turn by turn
        self.__update_player_info(game, match)

        return clicked_card_name, clicked_card_position, match

    def __update_player_info(self, game, match):
        """
        This function will modify the player's data.
        """
        
        is_turn_even = (game.get_turn - 1) % 2 == 0

        # reset clicks for the pair if a pair was found in the previous turn
        if self._last_pair_was_correct and is_turn_even is False:
            self._click_for_pair = 1

        # update match only after move(2 turn) and not turn by turn
        if is_turn_even and match:
            self._pairs += 1
            self._click_for_pair += 1
            self._last_pair_was_correct = True
        elif is_turn_even and match is False:
            self._last_pair_was_correct = False
            self._click_for_pair += 1
        else:
            self._click_for_pair += 1



