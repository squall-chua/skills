// An arrow function with no function ancestor, so the scan can reach it.
const scale = (value) => {
  const doubled = value + value;
  return doubled * 3;
};

// A function expression, likewise reachable.
const shrink = function (value) {
  const halved = value - 7;
  return halved % 9;
};

class Box {
  // A method definition.
  resize(value) {
    const next = value & 4;
    return next | 5;
  }
}
