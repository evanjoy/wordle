#!python3

from enum import Enum
import fileinput
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple
from multiprocessing import Pool

from tkinter import *
from tkinter import ttk
import tkinter.font as tkFont
from functools import partial

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

    def __getitem__(self, key):
        if key == "word":
            return self.word
        if key == "score":
            return self.score
        return None

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
    def process_clues(word_chars: str, clues: List[Tuple[int, str]]):
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
        print(word)
        print(str(clues))
        val = Constraint.process_clues(word, clues)
        print(str(val))
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
    constraints: Constraint
    favorites: List[str]
    phase: TurnPhase
    recommendations: List[Candidate]
    game_status: GameStatus
    turn_number: int
    words: List[str]

    def __init__(self) -> None:
        self.colors = []
        self.constraints = Constraint()
        # self.favorites = []
        # self.favorites = ["alien", "pouty", "fries"]
        self.favorites = list(map(lambda x: x.strip().lower(), open("favorites.txt", "r")))
        self.game_status = GameStatus.in_progress
        self.phase = TurnPhase.word_entry
        self.recommendations = []
        self.processCandidates()
        self.turn_number = -1
        self.words = []
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

    @staticmethod # was do_score()
    def getScoreForGuess(guess_candidate_pair):
        guess, candidates = guess_candidate_pair
        # total_matched = 0
        # total_candidate = 0
        total = 0
        for mystry in candidates:
            if guess == mystry:
                continue
            cons = Constraint.diff(mystry, guess)
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
        sorted_recs.sort(reverse=True, key=lambda x: x["score"])
        self.sorted_score = list(map(lambda x: x.word, sorted_recs))
        self.sorted_alpha = self.sorted_score[:]
        self.sorted_alpha.sort()

    def generateCandidates(self) -> None:
        self.constraints &= Constraint.fromWordAndCharModes(
            self.words[self.turn_number],
            self.colors[self.turn_number]
        )

        candidates = list(filter(self.constraints.match, self.allowed_word_list))

        with Pool() as p:
            score_pairs = list(
                p.imap_unordered(
                    GameModel.getScoreForGuess, map(lambda guess: (guess, candidates), candidates)
                )
            )

        score_pairs.sort(key=lambda x: x[1], reverse=True)

        print(str(score_pairs))
        self.recommendations = list(map(lambda pair: Candidate(pair[0], pair[1]), score_pairs))

    def processColors(self) -> GameStatus:
        # TODO: do it.  - take input, decide fail / not fail, then calculate next recommendations if needed
     
        self.generateCandidates()
        self.processCandidates()

        self.phase = TurnPhase.word_entry
        return self.game_status

    def addWord(self, word) -> str:
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



# Non-GUI code

# def do_score(args):
#     guess, candidates = args
#     # total_matched = 0
#     # total_candidate = 0
#     total = 0
#     for mystry in candidates:
#         if guess == mystry:
#             continue
#         cons = Constraint.diff(mystry, guess)
#         total += cons.score()
#     return guess, total / len(candidates)

# def make_guess(candidates, constraints):
#     candidates = list(filter(constraints.match, candidates))

#     with Pool() as p:
#         scores = list(
#             p.imap_unordered(
#                 do_score, map(lambda guess: (guess, candidates), candidates)
#             )
#         )

#     scores.sort(key=lambda x: x[1], reverse=True)
#     return list(map(lambda x: x[0], scores))

# def solve(mystry):
#     starting = "adieu"
#     candidates = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
#     constraints = Constraint.diff(mystry, starting)
#     rounds = 1
#     print(mystry)
#     print(f"\t{starting}")
#     while True:
#         guesses = make_guess(candidates, constraints)
#         if len(guesses) == 0:
#             break
#         rounds += 1
#         print(f"\t{guesses[0]}")
#         constraints &= Constraint.diff(mystry, guesses[0])
#     print(f"\t{rounds}")

# def daily():
#     constraints = Constraint()
#     for line in map(lambda x: x.strip().lower(), fileinput.input("input.txt")):
#         if line.startswith("#") or not line:
#             continue
#         constraints &= Constraint.fromString(line)

#     print(constraints)

#     words = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
#     hist = set(map(lambda x: x.strip().lower(), open("history.txt", "r")))
#     words -= hist
#     guesses = make_guess(words, constraints)
#     print("number of candidates", len(guesses))
#     for n in range(min(len(guesses), 20)):
#         guess = guesses[n]
#         print(guess)


# def historical():
#     words = set(map(lambda x: x.strip().lower(), open("words.txt", "r")))
#     for mystry in words:
#         solve(mystry)

# old command line way
#if __name__ == "__main__":
    # daily()


class Gui:
    def __init__(self, model):
        self.model = model
        self.entry_width = 325
        self.entry_height = 50
        self.word_select_width = 240
        self.word_select_width_chars=15
        self.word_select_height = 400
        self.word_select_items = None

    def buildPuzzleFrame(self, puzzle_frame):
        window_label = Label(puzzle_frame, text="Wordle Solver", font=("Helvetica", 24, "normal"))
        window_label.columnconfigure(1, weight=1)
        window_label.grid(column=0, row=0, columnspan=3)
        self.entry_row = Frame(puzzle_frame, width=self.entry_width, height=self.entry_height)
        self.entry_row.columnconfigure(1,weight=1)
        self.entry_row.grid(column=0, row=1, columnspan=3)
        self.entry_row.grid_propagate(0)
        self.entry_placeholder = Frame(puzzle_frame, width=self.entry_width, height=self.entry_height)
        self.entry_placeholder.grid_propagate(0)
        color_instruction = Label(self.entry_placeholder, text="Click to set letter colors")
        color_instruction.grid(column=0, row=0)
        self.entry_placeholder.columnconfigure(0, weight=1)
        self.entry_row.columnconfigure(1,weight=1)
        entry_label = Label(self.entry_row, text="Enter guess:")
        entry_label.grid(column=0, row=0)
        self.entry_input = Entry(self.entry_row, font=("Courier", 24, "normal"), width=5)
        self.entry_input.grid(column=1, row=0)
        board_frame = Frame(puzzle_frame)
        board_frame.grid(column=0, row=2, columnspan=3)
        row_pads = []
        self.row_letters = []

        self.color_confirm = Button(board_frame, text="Confirm", command=self.confirmColors)

        for row_index in range(6):
            row_pads.append(Label(board_frame, text=" ").grid(column=0, row=row_index))
            self.row_letters.append([])
            def rotate_color(e, row_index=0, col_index=0, widget=None):
                char_mode = model.changeColor(row_index, col_index)
                if char_mode is None:
                    return
                color_name = "gray61"
                if char_mode == CharMode.correct:
                    color_name="lime green"
                elif char_mode == CharMode.present:
                    color_name="gold"
                widget.config(bg=color_name)
            for col_index in range(5):
                letter_box = Label(
                    board_frame,
                    bg="white",
                    borderwidth=1,
                    fg="white",
                    font=("Courier", 32, "normal"),
                    relief="solid",
                    text=" ",
                    width=2,
                )
                letter_box.grid(column=col_index+1, row=row_index, padx=3, pady=3)
                self.row_letters[row_index].append(letter_box)
                letter_box.bind(
                    "<Button-1>",
                    partial(rotate_color, row_index=row_index, col_index=col_index, widget=letter_box)
                )
            row_pads.append(Label(board_frame, text=" ").grid(column=6, row=row_index))
            board_frame.columnconfigure(6, weight=1)

        quit_button = Button(board_frame, text="Quit", command=self.tk_root.destroy)
        quit_button.grid(column=0, row=8, columnspan=7)
        entry_button = Button(self.entry_row, text="Confirm", command=partial(self.confirmWord, input=self.entry_input))
        entry_button.grid(column=2, row=0)

    def buildPickerFrame(self, picker_frame):
        picker_frame.configure(width=self.word_select_width, height=self.word_select_height)
        picker_frame.pack_propagate(0)
        scrollbar_width = 16
        self.word_select_scrollbar = Scrollbar(picker_frame, orient="vertical")
        self.word_select_canvas = Canvas(
            picker_frame,
            width = self.word_select_width - scrollbar_width,
            yscrollcommand=self.word_select_scrollbar.set)
        self.word_select_canvas.pack(side="left", fill="y")
        self.word_select_canvas.columnconfigure(0, weight=1)
        self.word_list_frame = Frame(self.word_select_canvas, width=self.word_select_width-scrollbar_width)
        self.word_list_frame.pack(side='left', fill='y')
        self.word_list_frame.bind(
            "<Configure>",
            lambda e: self.word_select_canvas.configure(scrollregion=self.word_select_canvas.bbox("all"))
        )
        self.word_select_canvas.create_window((0, 0), window=self.word_list_frame, anchor="nw")
        self.word_select_scrollbar.config(command=self.word_select_canvas.yview)
        self.word_select_scrollbar.pack(side="right", fill="y")
        self.favorite_words_label = Label(self.word_list_frame,
            width=self.word_select_width_chars,
            height=1,
            text="Favorite Words")
        self.favorite_words_label.grid(column=0, row=0)
        list_start = 1
        for idx, word in enumerate(self.model.favorites):
            word_select_item = Label(self.word_list_frame, text=word, borderwidth=1, relief="raised")
            word_select_item.bind("<Button-1>", partial(self.word_select_item_click, text=word))
            word_select_item.grid(column=0, row=idx + list_start, ipadx = 5, ipady = 2, pady = 2)
        list_start += len(self.model.favorites)
        spacer_label = Label(self.word_list_frame, width=self.word_select_width_chars, text="")
        spacer_label.grid(column=0, row=list_start)
        self.candidate_words_label = Label(
            self.word_list_frame,
            width=self.word_select_width_chars,
            text="Suggested Words")
        self.candidate_words_label.grid(column=0, row=list_start + 1)
        sort_frame = Frame(self.word_list_frame)
        # Put button row after the label
        sort_frame.grid(column=0, row=list_start + 2)
        sort_label = Label(sort_frame, text="Sort: ")
        sort_label.grid(column=0, row=0)
        sort_alpha_button = Button(sort_frame, text="alpha", command=self.sortCandidatesByWord)
        sort_alpha_button.grid(column=1, row=0)
        sort_score_button = Button(sort_frame, text="score", command=self.sortCandidatesByScore)
        sort_score_button.grid(column=2, row=0)
        # Put word list after the label and sort button rows
        self.candidate_words_start_index = list_start + 3

    def buildUi(self):
        self.tk_root = Tk()

        puzzle_frame = Frame(self.tk_root)
        self.buildPuzzleFrame(puzzle_frame)
        puzzle_frame.grid(column=0, row=0)

        picker_frame = Frame(self.tk_root)
        self.buildPickerFrame(picker_frame)
        picker_frame.grid(column=1, row=0)

        self.populateWordRecommendations()

    def confirmWord(self, word_num=0, input=None):
        if input is None or len(self.row_letters) == 0:
            return False
        word = input.get().lower()
        if len(word) != 5:
            return False

        added_word = model.addWord(word)

        if added_word is None or added_word != word:
            return None

        for i in range(5):
            self.row_letters[model.turn_number][i].config(text=word[i].upper(), bg="gray61")

        self.color_confirm.grid(column=8, row=model.turn_number)
        self.entry_row.grid_forget()
        self.entry_placeholder.configure(width=self.entry_width, height=self.entry_height)
        self.entry_placeholder.grid(column=0, row=1, columnspan=3)
        self.entry_placeholder.grid_propagate(0)
        return True

    def confirmColors(self):
        turn_result = self.model.processColors()
        # TODO: do something with turn_result
        self.entry_input.delete(0, END)
        self.color_confirm.grid_forget()
        self.entry_placeholder.grid_forget()
        self.entry_row.grid(column=0, row=1)
        self.entry_row.grid_propagate(0)
        self.entry_row.configure(width=self.entry_width, height=self.entry_height)
        self.favorite_words_label.grid(column=0, row=0)
        self.populateWordRecommendations()

    def sortCandidatesByScore(self):
        self.populateWordRecommendations()

    def sortCandidatesByWord(self):
        self.populateWordRecommendations(True)

    def word_select_item_click(self, e, text=None):
        if text is None:
            return
        self.entry_input.delete(0, END)
        self.entry_input.insert(0, text)

    def populateWordRecommendations(self, sort_alpha=False):
        if self.word_select_items is None:
            self.word_select_items = []
        recommendations_list = model.getRecommendations(sortByScore = not sort_alpha)
        last_word_label = None
        for idx, word in enumerate(recommendations_list):
            if idx < len(self.word_select_items):
                label = self.word_select_items[idx]
                label.configure(text=word)
            else:
                label = Label(self.word_list_frame, text=word, borderwidth=1, relief="raised")
                label.grid(column=0, row=idx + self.candidate_words_start_index, ipadx = 5, ipady = 2, pady = 2)
                self.word_select_items.append(label)
            label.bind("<Button-1>", partial(self.word_select_item_click, text=word))
            last_word_label = label
        for idx in range(len(recommendations_list), len(self.word_select_items)):
            label = self.word_select_items[idx]
            label.unbind("<Button-1>")
            label.configure(text="")
            label.grid_forget()
        self.tk_root.update()

    def run_loop(self):
        self.tk_root.mainloop()

class Controller:
    def __init__(self, model, gui):
        self.model = model
        self.gui = gui
        gui.buildUi()

    def run_loop(self):
        gui.run_loop()

if __name__ == "__main__":
    model = GameModel()
    gui = Gui(model)
    controller = Controller(model, gui)

    controller.run_loop()


# UI goals and flow:
#  - Allow user to easily enter their words & results to solve Wordle quickly (algorithm borrowed from abersnazy to focus on UI work)
#  - Allow user to add any word(s) to list of favorite (starting) words
#  - Nice to have: "random" button populating UI from remaining allowable word(s)/letters(s) to get brain juices flowing
#  1 Request starting word from user
#    a Show nice text entry UI where user can type easily or click a handful of starting words
#    b Hide entry mechanism when word submitted.
#  2 Allow user to enter result (success, or colors of letters)
#  3 Deal with result
#    a If success, cheer!
#    b If fail and it was the 6th try, commiserate
#  4 Otherwise, update remaining constraints and calculate best next guesses
#  5 Allow user to choose next word by clicking on words in best guess list or favorite words list
#    a show list(s) and confirmation button once guesses are calculated
#    b model words in place when guesses are selected but unconfirmed
#    c hide list(s) once a selection is confirmed
#  6 Go back to step 2
