#!python3

import fileinput
from collections import Counter, defaultdict

at_least = defaultdict(lambda: 0)
allowed = [
    {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
     'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'},
    {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
     'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'},
    {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
     'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'},
    {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
     'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'},
    {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
     'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'},
]

used = set()

for line in map(lambda x: x.strip().lower(), fileinput.input("input.txt")):
    curr_at_least = defaultdict(lambda: 0)
    word = ""
    for pos in range(5):
        mode = line[2*pos]
        ltr = line[2*pos + 1]
        word += ltr
        if mode == '_':
            for allow in allowed:
                if ltr in allow:
                    allow.remove(ltr)
        else:
            if mode == '+':
                allowed[pos] = {ltr}
            elif ltr in allowed[pos]:
                allowed[pos].remove(ltr)
            curr_at_least[ltr] += 1
    used.add(word)

    for ltr, least in curr_at_least.items():
        at_least[ltr] = max(at_least[ltr], least)

# if len(used) == 0:
#     print("############ first guess")
#     print("adieu")
#     exit()

print("############ constraints")
print("words used:", used)
print("at least:", ", ".join([f"{c}:{ltr}" for ltr, c in at_least.items()]))
for pos in range(5):
    foo = list(allowed[pos])
    foo.sort()
    print(pos, ":", "".join(foo))

words = map(lambda x: x.strip().lower(), open('words.txt', 'r'))
candidates = []
for word in words:
    fail = False
    if word in used:
        fail = True
    word_has = Counter(word)
    for ltr, count in at_least.items():
        if word_has[ltr] < count:
            fail = True
    for pos, ltr in enumerate(word):
        if ltr not in allowed[pos]:
            fail = True
    if fail:
        continue
    # passed both tests
    candidates.append(word)

# compute letter frequence for each posistion
pos_ltr_freq = [Counter(), Counter(), Counter(), Counter(), Counter()]
for word in candidates:
    for pos, ltr in enumerate(word):
        pos_ltr_freq[pos][ltr] += 1
pos_tot = [sum(ltr_freq.values()) for ltr_freq in pos_ltr_freq]

print("############ scores for", len(candidates))
for pos in range(5):
    print([f"{ltr}:{freq*100//pos_tot[pos]}%" for ltr,
           freq in pos_ltr_freq[pos].most_common(10)])

guesses = []
for word in candidates:
    score = 0
    for pos, ltr in enumerate(word):
        score += pos_ltr_freq[pos][ltr] / pos_tot[pos]

    # halving those scores of the guesses with multiple of the same letter
    for ltr, count in Counter(word).items():
        if ((at_least[ltr] != 0 and count > at_least[ltr]) or
                (at_least[ltr] == 0 and count > 1)):
            score = score / 2

    guesses.append((word, score))
    guesses.sort(key=lambda guess: guess[1], reverse=True)
    if len(guesses) > 10:
        guesses.pop()

print("############ guesses")
print("\n".join(
    map(lambda word_score: f"{word_score[0]}: {round(word_score[1], 2)}", guesses)))
