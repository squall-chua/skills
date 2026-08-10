function interpolated(value) {
  // The only flippable operator in this file sits inside the interpolation.
  const detail = `n=${value + 1}`;
  const label = "plain";
  if (detail) {
    return detail;
  }
  return label;
}
