fun interpolated(value: Int): String {
    // The only flippable operator in this file sits inside the interpolation.
    val detail = "n=${value + 1}"
    val label = "plain"
    if (detail.isEmpty()) {
        return label
    }
    return detail
}
