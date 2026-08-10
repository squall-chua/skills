// Word operators, including the negated pattern form.
class Ops {
    bool WordA(object a, object b) { return a is string; }

    bool WordB(object a, object b) { return a is not string; }

    bool WordC(object a, object b) { return a as string != null; }
}
