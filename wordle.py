#!python3

from wordle_model import GameModel
from wordle_view_controller import Controller, Gui

if __name__ == "__main__":
    model = GameModel()
    gui = Gui(model)
    controller = Controller(model, gui)

    controller.run_loop()
