class Interp
{
    string Interpolated(int value)
    {
        // The only flippable operator in this file sits inside the interpolation.
        string detail = $"n={value + 1}";
        string label = "plain";
        if (string.IsNullOrEmpty(detail))
        {
            return label;
        }
        return detail;
    }
}
