fun alpha(value: Int): String {
    // Only alpha carries a comment. Comments are spelling, so beta must still match it.
    val label = "alpha: "
    val total = value + 1
    if (total > 10) {
        return label + total.toString()
    }
    return label
}

fun beta(number: Int): String {
    val tag = "beta: "
    val amount = number + 2
    if (amount > 20) {
        return tag + amount.toString()
    }
    return tag
}
