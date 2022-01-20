#!python3

from enum import Enum
import fileinput
from collections import Counter, defaultdict
from typing import Dict, List, Set
from multiprocessing import Pool


class Mode(Enum):
    absent = "_"
    present = "-"
    correct = "+"


class Constraint:
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
    def parse(line: str) -> None:
        out = Constraint()
        out.used.add("".join(map(line.__getitem__, range(1, 10, 2))))

        clues = []
        for pos in range(0, 10, 2):
            mode = Mode(line[pos])
            ltr = line[pos + 1]
            clues.append((pos // 2, mode, ltr))

        for pos, mode, ltr in filter(lambda x: x[1] == Mode.absent, clues):
            for allow in out.allows:
                allow.discard(ltr)
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.present, clues):
            for allow in out.allows:
                allow.add(ltr)
            out.allows[pos].discard(ltr)
            out.at_least[ltr] = out.at_least.get(ltr, 0) + 1
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.absent, clues):
            out.allows[pos].discard(ltr)
        for pos, mode, ltr in filter(lambda x: x[1] == Mode.correct, clues):
            out.allows[pos] = {ltr}
            out.at_least[ltr] = out.at_least.get(ltr, 0) + 1

        return out

    @staticmethod
    def diff(mystry, guess: str):
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
            v: Mode.correct if k == v else Mode.present
            for k, v in enumerate(mapping)
            if v != -1
        }

        clues = "".join(
            [rmapping.get(pos, Mode.absent).value + guess[pos] for pos in range(5)]
        )

        return Constraint.parse(clues)

    def __and__(self, othr):
        return Constraint(
            {
                k: max(othr.at_least.get(k, 0), self.at_least.get(k, 0))
                for k in self.at_least | othr.at_least
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


def do_score(args):
    guess, candidates = args
    # total_matched = 0
    # total_candidate = 0
    total = 0
    for mystry in candidates:
        if guess == mystry:
            continue
        cons = Constraint.diff(mystry, guess)
        total += cons.score()
    return guess, total / len(candidates)


def make_guess(candidates, constraints):
    candidates = list(filter(constraints.match, candidates))

    with Pool() as p:
        scores = list(
            p.imap_unordered(
                do_score, map(lambda guess: (guess, candidates), candidates)
            )
        )

    scores.sort(key=lambda x: x[1], reverse=True)
    return list(map(lambda x: x[0], scores))


def solve(mystry):
    starting = "adieu"
    candidates = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    constraints = Constraint.diff(mystry, starting)
    rounds = 1
    print(mystry)
    print(f"\t{starting}")
    while True:
        guesses = make_guess(candidates, constraints)
        if len(guesses) == 0:
            break
        rounds += 1
        print(f"\t{guesses[0]}")
        constraints &= Constraint.diff(mystry, guesses[0])
    print(f"\t{rounds}")


def daily():
    constraints = Constraint()
    for line in map(lambda x: x.strip().lower(), fileinput.input("input.txt")):
        if line.startswith("#") or not line:
            continue
        constraints &= Constraint.parse(line)

    print(constraints)

    words = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    hist = set(map(lambda x: x.strip().lower(), open("history.txt", "r")))
    words -= hist
    guesses = make_guess(words, constraints)
    print("number of candidates", len(guesses))
    for n in range(min(len(guesses), 20)):
        guess = guesses[n]
        print(guess)


def historical():
    words = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
    for mystry in words:
        solve(mystry)


if __name__ == "__main__":
    daily()
