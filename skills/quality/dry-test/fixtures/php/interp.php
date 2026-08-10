<?php

// The only flippable operator in this file sits inside the interpolation, so the check
// cannot accidentally test some other operator instead.
//
// PHP's curly syntax takes a *variable* — `"{$a + 1}"` is not valid PHP, whatever the
// grammar accepts — so the operator has to ride inside an array subscript, which is a
// full expression.
function interpolated($values, $index) {
    $detail = "n={$values[$index + 1]}";
    $label = "plain";
    if ($detail) {
        return $detail;
    }
    return $label;
}
