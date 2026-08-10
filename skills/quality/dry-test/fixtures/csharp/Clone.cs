class Clone
{
    string Alpha(int value)
    {
        // Only Alpha carries a comment. Comments are spelling, so Beta must still match it.
        string label = "alpha: ";
        int total = value + 1;
        if (total > 10)
        {
            return label + total.ToString();
        }
        return label;
    }

    string Beta(int number)
    {
        string tag = "beta: ";
        int amount = number + 2;
        if (amount > 20)
        {
            return tag + amount.ToString();
        }
        return tag;
    }
}
