def interpolated(value):
    # The only flippable operator in this file sits inside the interpolation, so the
    # check cannot accidentally test some other operator instead.
    detail = f"n={value + 1}"
    label = "plain"
    if detail:
        return detail
    return label
