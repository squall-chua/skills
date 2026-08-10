// Word operators, and the negated forms the grammar spells with a leading `!`.
fun wordA(a: Any, b: List<Any>): Boolean = a in b

fun wordB(a: Any, b: List<Any>): Boolean = a !in b

fun wordC(a: Any, b: List<Any>): Boolean = a is String

fun wordD(a: Any, b: List<Any>): Boolean = a !is String
