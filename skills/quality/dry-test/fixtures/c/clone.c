#include <stdio.h>

int alpha(int value) {
    // Only alpha carries a comment. Comments are spelling, so beta must still match it.
    const char *label = "alpha: ";
    int total = value + 1;
    if (total > 10) {
        printf("%s%d", label, total);
        return total;
    }
    return value;
}

int beta(int number) {
    const char *tag = "beta: ";
    int amount = number + 2;
    if (amount > 20) {
        printf("%s%d", tag, amount);
        return amount;
    }
    return number;
}
