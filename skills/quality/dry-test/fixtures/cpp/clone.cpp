#include <string>

std::string alpha(int value) {
    // Only alpha carries a comment. Comments are spelling, so beta must still match it.
    std::string label = "alpha: ";
    int total = value + 1;
    if (total > 10) {
        return label + std::to_string(total);
    }
    return label;
}

std::string beta(int number) {
    std::string tag = "beta: ";
    int amount = number + 2;
    if (amount > 20) {
        return tag + std::to_string(amount);
    }
    return tag;
}
