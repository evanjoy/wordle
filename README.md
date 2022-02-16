# WORDLE SOLVER

This fork is a full UI around abersnaze's wordle guess-generator (https://github.com/abersnaze/wordle)

It's mostly an exercise for learning tkinter with something other than a vanilla UI with only text inputs and labels.

![UI screenshot](https://github.com/evanjoy/wordle/blob/main/screenshot_suggestion.png)

You can use it to help play the real Wordle.  Or you can play "backwards-wordle" with it where you pick the secret word and then see how the solver acts.  See if you can stump it!

## INPUT

This tool alternates between:
 - Word selection - tell the solver what word you guessed
 - Color entry - tell the solver what colors Wordle assigned to the letters
 - Generating guesses - giving you a list of words to try next

### Picking a word
You can click a word in the Favorites or Suggestions section, or type it in to the input box at the top. Then click the confirm button.  There are currently no suggestions implemented for the first word.  Just pick one of your favorites or type a word.  Many people like to start with "adieu" to get most of the vowels out of the way.

### Setting colors
After entering a word, you tell the solver what Wordle said about each letter in that word so that it can generate the next guesses.

Clicking a letter will cycle between gray, yellow, and green.

Once it matches what shows up in your actual Wordle game, click Confirm.

## RUNNING

`./wordle.py`

When you confirm the colors on the first word, it might take up to 20 seconds to go through the possibilities.

(Note: this version doesn't currently use history.txt)

## Configuration

Put words you like to start the game with in favorites.txt, and they'll show up in the favorites section of the word picker.
