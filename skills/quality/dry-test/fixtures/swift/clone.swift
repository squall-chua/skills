func alpha(value: Int) -> String {
    // Only alpha carries a comment. Comments are spelling, so beta must still match it.
    let label = "alpha: "
    let total = value + 1
    if total > 10 {
        return label + String(total)
    }
    return label
}

func beta(number: Int) -> String {
    let tag = "beta: "
    let amount = number + 2
    if amount > 20 {
        return tag + String(amount)
    }
    return tag
}
