def alpha(value)
  # Only alpha carries a comment. Comments are spelling, so beta must still match it.
  label = "alpha: "
  total = value + 1
  if total > 10
    return label + total.to_s
  end
  label
end

def beta(number)
  tag = "beta: "
  amount = number + 2
  if amount > 20
    return tag + amount.to_s
  end
  tag
end
