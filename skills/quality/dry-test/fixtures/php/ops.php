<?php
// Word operators. Each differs from its neighbour in that one operator only.
function wordA($a, $b) { return $a instanceof DateTime; }

function wordB($a, $b) { return $a and $b; }

function wordC($a, $b) { return $a or $b; }

function wordD($a, $b) { return $a xor $b; }
