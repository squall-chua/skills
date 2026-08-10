def interpolated(value)
  # The only flippable operator in this file sits inside the interpolation.
  detail = "n=#{value + 1}"
  label = "plain"
  if detail.empty?
    return label
  end
  detail
end
