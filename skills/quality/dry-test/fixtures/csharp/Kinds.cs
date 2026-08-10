// Top-level statements come first, so this local function has no method ancestor and the
// scan can actually reach it. Inside a method body it would be swallowed by the method.
int Scale(int value)
{
    int doubled = value + value;
    return doubled * 3;
}

class Kinds
{
    private readonly int seed;

    // A constructor, so this file exercises the constructor_declaration entry in UNITS.
    Kinds(int value)
    {
        if (value > 0)
        {
            this.seed = value + 1;
        }
        else
        {
            this.seed = 0;
        }
    }
}
