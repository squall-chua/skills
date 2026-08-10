func interpolated(value: Int) -> String {
    // The only flippable operator in this file sits inside the interpolation.
    let detail = "n=\(value + 1)"
    let label = "plain"
    if detail.isEmpty {
        return label
    }
    return detail
}
