#!python3

from abc import abstractmethod
import unittest
from unittest.mock import Mock
from wordle_model import GameModel, CharMode, ConstraintAbstract
from typing import List

class ConstraintMock(ConstraintAbstract):
    @staticmethod
    def fromString(line: str) -> ConstraintAbstract:
        return None

    @staticmethod
    def fromWordAndCharModes(word: str, modes: List[CharMode]) -> ConstraintAbstract:
        return None

    @staticmethod
    def process_clues(word_chars, clues):
        return None

    @staticmethod
    def diff(mystery, guess):
        return ConstraintMock()
    
    def score(self):
        return 10.0

    def __and__(self, other:ConstraintAbstract):
        return self

    def __repr__(self):
        return "ConstraintMock"
    
    def match(self, word: str):
        return True


word_list = ["brand", "adieu", "candy"]

class testWordleModel(unittest.TestCase):

    def create_model(self):
        self.mock_constraint = unittest.mock.create_autospec(spec=ConstraintAbstract)
        self.mock_constraint.filter = Mock(return_value=True)
        self.mock_constraint.__and__=Mock(return_value=self.mock_constraint)
        return GameModel(word_list=word_list, constraint_class=ConstraintMock, constraint=self.mock_constraint, use_pool=False)

    def test_default(self):
        pass

    def test_it_can_construct(self):
        model = self.create_model()

    def test_next_char_mode_absent_goes_to_present(self):
        self.assertEqual(GameModel.getNextMode(CharMode.absent), CharMode.present)

    def test_next_char_mode_present_goes_to_correct(self):
        self.assertEqual(GameModel.getNextMode(CharMode.present), CharMode.correct)

    def test_next_char_mode_correct_goes_to_absent(self):
        self.assertEqual(GameModel.getNextMode(CharMode.correct), CharMode.absent)

    def test_enter_first_word(self):
        first_word = "asdfg"
        model = self.create_model()
        result = model.addWord(first_word)
        self.assertEqual(result, first_word)

    def test_enter_colors_before_first_word_does_nothing(self):
        model = self.create_model()
        turn = 0
        letter_index = 2
        result = model.changeColor(turn, letter_index)
        self.assertIsNone(result)

    def test_enter_second_word_before_colors_does_nothing(self):
        first_word = "asdfg"
        model = self.create_model()
        result = model.addWord(first_word)
        self.assertEqual(result, first_word)
        second_word = "belts"
        result = model.addWord(second_word)
        self.assertIsNone(result)

    def test_submitting_word_and_colors_returns_word_list(self):
        model = self.create_model()

        # add a word
        model.addWord("word1")
        # Leave it at a default (all gray) letter status

        # Then process possibilities & generate candidates
        # by default the scorer generates identical scores and 
        # all words in the list are passed, so we should get the
        # original word list in sorted order if we sort alpha
        model.generateCandidates()
        model.processCandidates()
        recs = model.getRecommendations(False)
        sorted_word_list = word_list.copy()
        sorted_word_list.sort()
        self.assertEqual(recs, sorted_word_list)
        
    def test_submitting_word_and_colors_returns_filtered_word_list(self):
        model = self.create_model()
        self.mock_constraint.match = Mock(return_value=False)

        # add a word
        model.addWord("word1")
        # Leave it at a default (all gray) letter status

        # Then process possibilities & generate candidates.
        # We set it so all words get filtered out,
        # so we should get an empty list
        model.generateCandidates()
        model.processCandidates()
        recs = model.getRecommendations(False)
        self.assertEqual(0, len(recs))
        

if __name__ == "__main__":
    unittest.main()
