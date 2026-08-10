class Kinds {
    private final int seed;

    // A constructor, so this file exercises the constructor_declaration entry in UNITS.
    Kinds(int value) {
        if (value > 0) {
            this.seed = value + 1;
        } else {
            this.seed = 0;
        }
    }
}
