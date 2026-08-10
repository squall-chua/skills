<?php

function alpha($value) {
    // Only alpha carries a comment. Comments are spelling, so beta must still match it.
    $label = "alpha: ";
    $total = $value + 1;
    if ($total > 10) {
        return $label . strval($total);
    }
    return $label;
}

function beta($number) {
    $tag = "beta: ";
    $amount = $number + 2;
    if ($amount > 20) {
        return $tag . strval($amount);
    }
    return $tag;
}
