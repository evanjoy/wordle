# WORDLE SOLVER
This wordle solver is meant to be run once for each guess. The program tells you what to guess in turn you feed it the clues and it will tell you what to guess next.

## INPUT

if you guess `WEARY` and the `W` is in the right spot put a `+` (plus) the response as

> `+W_E_A_R_Y`

if you guess `PILLS` and the letter `I` is in the word but in the wrong spot encode it with `-` (minus) like

> `_P-I_L_L_S`

for all the letters that aren't in the word you prefix with an `_` (underscore)

## RUNNING
once the `input.txt` is saved run the program to get the next guess.

`./wordle.py`

for the first guess it is hard coded to `ADIEU` because all the vowels seems like a good idea.

## FUTURE PLANS
* analsis on best first guess.
