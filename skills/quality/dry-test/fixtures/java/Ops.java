// `instanceof` is Java's only word operator, so the pair below differs by more than
// one token. The declared-operator check is what gates it.
class Ops {
    boolean wordA(Object a, Object b) { return a instanceof String; }

    boolean wordB(Object a, Object b) { return a == b; }
}
