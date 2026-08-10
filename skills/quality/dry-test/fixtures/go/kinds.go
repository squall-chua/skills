package fixture

type counter struct{ total int }

// A method, so this file exercises the method_declaration entry in UNITS.
func (c *counter) bump(step int) int {
	if step > 0 {
		c.total = c.total + step
	}
	return c.total
}
