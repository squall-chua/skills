class Kinds
  # A singleton method, so this file exercises the singleton_method entry in UNITS.
  def self.bump(step)
    total = step + 1
    if total > 10
      return total
    end
    total
  end
end
