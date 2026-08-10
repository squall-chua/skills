package fixture

import "strconv"

func Alpha(value int) string {
	// Only Alpha carries a comment. Comments are spelling, so Beta must still match it.
	label := "alpha: "
	total := value + 1
	if total > 10 {
		return label + strconv.Itoa(total)
	}
	return label
}

func Beta(number int) string {
	tag := "beta: "
	amount := number + 2
	if amount > 20 {
		return tag + strconv.Itoa(amount)
	}
	return tag
}
