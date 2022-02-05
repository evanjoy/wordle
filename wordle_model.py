#!python3

from __future__ import annotations

from abc import ABC, abstractmethod, abstractclassmethod
from collections import Counter, defaultdict
from enum import Enum
import fileinput
from typing import Dict, List, Set, Tuple
from multiprocessing import Pool

class CharMode(Enum):
    absent = "_"
    present = "-"
    correct = "+"
    num_modes = 3

class Candidate:
    word: str
    score: int

    def __init__(self, word=None, score=0):
        self.word = word
        self.score = score

class ConstraintAbstract(ABC):
    @staticmethod
    @abstractmethod
    def process_clues(word_chars: str, clues: List[Tuple[int, str]]):
        return None

    @staticmethod
    @abstractmethod
    def fromWordAndCharModes(word: str, modes: List[CharMode]) -> ConstraintAbstract:
        return None

    @staticmethod
    @abstractmethod
    def fromString(line: str) -> ConstraintAbstract:
        return None

    @staticmethod
    @abstractmethod
    def diff(mystry, guess: str) -> ConstraintAbstract:
        return None

    @abstractmethod
    def __and__(self, othr):
        return self

    @abstractmethod
    def __repr__(self) -> str:
        return "ConstraintAbstract"

    @abstractmethod
    def match(self, word: str) -> bool:
        return False

    @abstractmethod
    def score(self) -> float:
        return 0.0

# Constraint class borrowed from @abersnaze; refactored only minorly since this project is more a learning experience about tkinter and python 3.x features.
class Constraint(ConstraintAbstract):
    at_least: Dict[str, int]
    allows: List[Set[str]]
    used: Set[str]

    def __init__(
        self,
        at_least=None,
        allows=None,
        used=None,
    ) -> None:
        self.at_least = at_least if at_least else {}
        self.allows = (
            allows
            if allows
            else [
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
                set(map(chr, range(97, 123))),
            ]
        )
        self.used = used if used else set()

    @staticmethod
    def process_clues(word_chars: str, clues: List[Tuple[int, str]]) -> ConstraintAbstract:
        result = Constraint()
        for pos, mode, ltr in filter(lambda x: x[1] == CharMode.absent, clues):
            for allow in result.allows:
                allow.discard(ltr)
        for pos, mode, ltr in filter(lambda x: x[1] == CharMode.present, clues):
            for allow in result.allows:
                allow.add(ltr)
            result.allows[pos].discard(ltr)
            result.at_least[ltr] = result.at_least.get(ltr, 0) + 1
        for pos, mode, ltr in filter(lambda x: x[1] == CharMode.absent, clues):
            result.allows[pos].discard(ltr)
        for pos, mode, ltr in filter(lambda x: x[1] == CharMode.correct, clues):
            result.allows[pos] = {ltr}
            result.at_least[ltr] = result.at_least.get(ltr, 0) + 1
        return result

    @staticmethod
    def fromWordAndCharModes(word: str, modes: List[CharMode]) -> None:
        result = Constraint()
        result.used.add("".join(map(word.__getitem__, range(5))))
        clues = []
        for char_index in range(5):
            mode = modes[char_index]
            ltr = word[char_index]
            clues.append((char_index, mode, ltr))
        val = Constraint.process_clues(word, clues)
        return val

    @staticmethod
    def fromString(line: str) -> None:
        word_chars = "".join(map(line.__getitem__, range(1, 10, 2)))

        clues = []
        for pos in range(0, 10, 2):
            mode = CharMode(line[pos])
            ltr = line[pos + 1]
            clues.append((pos // 2, mode, ltr))

        return Constraint.process_clues(word_chars, clues)

        return result

    @staticmethod
    def diff(mystry, guess: str) -> ConstraintAbstract:
        mguess = guess
        mapping = [-1, -1, -1, -1, -1]
        for pos in range(5):
            if mystry[pos] == mguess[pos]:
                mapping[pos] = pos
                mguess = mguess[:pos] + "_" + mguess[pos + 1 :]
        for pos in range(5):
            if mapping[pos] != -1:
                continue
            ltr = mystry[pos]
            to_pos = mapping[pos] = mguess.find(ltr)
            if to_pos != -1:
                mguess = mguess[:to_pos] + "_" + mguess[to_pos + 1 :]

        rmapping = {
            v: CharMode.correct if k == v else CharMode.present
            for k, v in enumerate(mapping)
            if v != -1
        }

        clues = "".join(
            [rmapping.get(pos, CharMode.absent).value + guess[pos] for pos in range(5)]
        )

        return Constraint.fromString(clues)

    def __and__(self, othr):
        return Constraint(
            {
                k: max(othr.at_least.get(k, 0), self.at_least.get(k, 0))
                for k in self.at_least or othr.at_least
            },
            list(map(lambda a: a[0].intersection(a[1]), zip(self.allows, othr.allows))),
            self.used.union(othr.used),
        )

    def __repr__(self) -> str:
        pass
        out = f"words used: [{', '.join(self.used)}], "
        out += f"at least: [{', '.join([f'{c}:{ltr}' for ltr, c in self.at_least.items()])}], "
        out += f"allowed: [{', '.join(map(str, map(len, self.allows)))}]"
        return out

    def match(self, word: str) -> bool:
        fail = False
        if word in self.used:
            fail = True
        word_has = Counter(word)
        for ltr, count in self.at_least.items():
            if word_has[ltr] < count:
                fail = True
        for pos, ltr in enumerate(word):
            if ltr not in self.allows[pos]:
                fail = True
        return not fail

    def score(self):
        """
        how specific the constraints are. inverse how many letters are
        allowed in each posision. if all 26 letters are allowed then
        the score is 1/26. if only one letter is allowed then the score
        is 1/1.
        """
        return sum(map(lambda allow: 1 / len(allow), self.allows))

class TurnPhase(Enum):
    word_entry = 0
    color_entry = 1

class GameStatus(Enum):
    in_progress = 0
    over_success = 1
    over_failure = 2

class GameModel:
    colors: List[List[CharMode]]
    constraint_class: type
    constraints: ConstraintAbstract
    favorites: List[str]
    phase: TurnPhase
    recommendations: List[Candidate]
    game_status: GameStatus
    turn_number: int
    use_pool: bool
    words: List[str]

    def __init__(self, word_list:List[str] = None, favorites_list:List[str] = None, constraint_class:type = Constraint, constraint:ConstraintAbstract = None, use_pool:bool = True) -> None:
        self.colors = []
        self.constraint_class = constraint_class
        if constraint is not None:
            self.constraints = constraint
        else:
            self.constraints = constraint_class()
        if favorites_list is not None:
            self.favorites = favorites_list
        else:
            self.favorites = list(map(lambda x: x.strip().lower(), open("favorites.txt", "r")))
        self.game_status = GameStatus.in_progress
        self.phase = TurnPhase.word_entry
        self.recommendations = []
        self.processCandidates()
        self.turn_number = -1
        self.use_pool = use_pool
        self.words = []
        if word_list is not None:
            self.allowed_word_list = word_list
        else:
            self.allowed_word_list = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))

    def incrementTurn(self) -> None:
        self.turn_number += 1

    @staticmethod
    def getNextMode(mode: CharMode) -> CharMode:
        return {
            CharMode.absent: CharMode.present,
            CharMode.present: CharMode.correct,
            CharMode.correct: CharMode.absent
        }.get(mode, CharMode.absent)

    def getScoreForGuess(self, guess_candidate_pair):
        guess, candidates = guess_candidate_pair
        # total_matched = 0
        # total_candidate = 0
        total = 0
        for mystry in candidates:
            if guess == mystry:
                continue
            cons = self.constraint_class.diff(mystry, guess)
            total += cons.score()
        return guess, total / len(candidates)

    def changeColor(self, turn, index) -> CharMode:
        if self.phase != TurnPhase.color_entry:
            return None
        if len(self.colors) != turn + 1:
            return None
        self.colors[turn][index] = GameModel.getNextMode(self.colors[turn][index])
        return self.colors[turn][index]

    def processCandidates(self) -> None:
        sorted_recs = self.recommendations[:]
        sorted_recs.sort(reverse=True, key=lambda x: x.score)
        self.sorted_score = list(map(lambda x: x.word, sorted_recs))
        self.sorted_alpha = self.sorted_score[:]
        self.sorted_alpha.sort()

    def generateCandidates(self) -> None:
        self.constraints &= self.constraint_class.fromWordAndCharModes(
            self.words[self.turn_number],
            self.colors[self.turn_number]
        )

        candidates = list(filter(self.constraints.match, self.allowed_word_list))

        calc_function = self.getScoreForGuess
        params_list = map(lambda guess: (guess, candidates), candidates)
        if self.use_pool:
            with Pool() as p:
                score_pairs = list(p.imap_unordered(calc_function, params_list))
        else:
            score_pairs = []
            for params in params_list:
                score_pairs.append(calc_function(params))


        score_pairs.sort(key=lambda x: x[1], reverse=True)

        self.recommendations = list(map(lambda pair: Candidate(pair[0], pair[1]), score_pairs))

    def processColors(self) -> GameStatus:
        self.generateCandidates()
        self.processCandidates()

        self.phase = TurnPhase.word_entry
        return self.game_status

    def addWord(self, word) -> str:
        if self.phase != TurnPhase.word_entry:
            return None
        if len(self.words) <= self.turn_number:
            return None
        if len(word) != 5:
            return None

        self.incrementTurn()
        self.words.append(word.lower())
        self.phase = TurnPhase.color_entry
        self.colors.append([CharMode.absent]*5)

        return self.words[-1]

    def getRecommendations(self, sortByScore=True):
        if sortByScore:
            return self.sorted_score
        return self.sorted_alpha


