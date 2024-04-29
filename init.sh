#!/bin/bash

rm -f west.h5 binbounds.txt
BSTATES="--bstate initial,1,pi/4"
TSTATES="--tstate final,2.357"
w_init $BSTATES $TSTATES "$@"
