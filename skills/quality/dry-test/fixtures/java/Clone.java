class Clone {
    String alpha(int value) {
        // Only alpha carries a comment. Comments are spelling, so beta must still match it.
        String label = "alpha: ";
        int total = value + 1;
        if (total > 10) {
            return label + Integer.toString(total);
        }
        return label;
    }

    String beta(int number) {
        String tag = "beta: ";
        int amount = number + 2;
        if (amount > 20) {
            return tag + Integer.toString(amount);
        }
        return tag;
    }
}
