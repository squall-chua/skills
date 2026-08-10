fn alpha(value: i32) -> String {
    // Only alpha carries a comment. Comments are spelling, so beta must still match it.
    let label = String::from("alpha: ");
    let total = value + 1;
    if total > 10 {
        return label + &total.to_string();
    }
    label
}

fn beta(number: i32) -> String {
    let tag = String::from("beta: ");
    let amount = number + 2;
    if amount > 20 {
        return tag + &amount.to_string();
    }
    tag
}
