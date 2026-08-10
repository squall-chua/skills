<?php

class Kinds {
    private $seed = 0;

    // A method, so this file exercises the method_declaration entry in UNITS.
    public function bump($step) {
        if ($step > 0) {
            $this->seed = $this->seed + $step;
        }
        return $this->seed;
    }
}
