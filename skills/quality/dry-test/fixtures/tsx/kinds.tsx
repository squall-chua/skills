// An arrow function with no function ancestor, so the scan can reach it.
const scale = (value: number): number => {
  const doubled = value + value;
  return doubled * 3;
};

// A function expression, likewise reachable.
const shrink = function (value: number): number {
  const halved = value - 7;
  return halved % 9;
};

class Box {
  // A method definition.
  resize(value: number): number {
    const next = value & 4;
    return next | 5;
  }
}
