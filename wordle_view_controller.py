#!python3

from tkinter import *
from tkinter import ttk
import tkinter.font as tkFont
from functools import partial

from wordle_model import GameModel, CharMode

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


class Gui:
    def __init__(self, model: GameModel):
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
                char_mode = self.model.changeColor(row_index, col_index)
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

        added_word = self.model.addWord(word)

        if added_word is None or added_word != word:
            return None

        for i in range(5):
            self.row_letters[self.model.turn_number][i].config(text=word[i].upper(), bg="gray61")

        self.color_confirm.grid(column=8, row=self.model.turn_number)
        self.entry_row.grid_forget()
        self.entry_placeholder.configure(width=self.entry_width, height=self.entry_height)
        self.entry_placeholder.grid(column=0, row=1, columnspan=3)
        self.entry_placeholder.grid_propagate(0)
        return True

    def confirmColors(self):
        turn_result = self.model.processColors()
        # TODO: do something with turn_result - could show a fanfare or a sad face if the game is over
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
        recommendations_list = self.model.getRecommendations(sortByScore = not sort_alpha)
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
        self.gui.run_loop()


