// Word operators. Each differs from its neighbour in that one operator only.
function wordA(a, b, c) {
  return a in b;
}

function wordB(a, b, c) {
  return a instanceof b;
}
