function alpha(value: number): string {
  // Only alpha carries a comment. Comments are spelling, so beta must still match it.
  const label = "alpha: ";
  const total = value + 1;
  if (total > 10) {
    return label + String(total);
  }
  return label;
}

function beta(number: number): string {
  const tag = "beta: ";
  const amount = number + 2;
  if (amount > 20) {
    return tag + String(amount);
  }
  return tag;
}
