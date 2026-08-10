# Operators the character test cannot see: word operators, and chained comparisons,
# which hang two operator tokens off one node. Each function differs from its
# neighbours in that one operator and in nothing else, so any two of them
# fingerprinting alike means the operator never reached a tag.
def word_a(a, b, c):
    return a in b


def word_b(a, b, c):
    return a not in b


def word_c(a, b, c):
    return a is b


def word_d(a, b, c):
    return a is not b


def word_e(a, b, c):
    return a and b


def word_f(a, b, c):
    return a or b


def chain_a(a, b, c):
    return a < b < c


def chain_b(a, b, c):
    return a > b > c


def chain_c(a, b, c):
    return a < b > c
