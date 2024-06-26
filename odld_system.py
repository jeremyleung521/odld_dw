from __future__ import print_function, division
import logging

import numpy as np
from numpy import sin, cos, tan, exp
from numpy.random import normal as random_normal

from westpa.core.binning import RectilinearBinMapper
from westpa.core.propagators import WESTPropagator
from westpa.core.systems import WESTSystem

from westpa.core.propagators import WESTPropagator
from westpa.core.systems import WESTSystem
from westpa.core.binning import RectilinearBinMapper
from westpa.core.binning import RecursiveBinMapper

PI = np.pi
log = logging.getLogger("westpa.rc")

pcoord_len = 21
pcoord_dtype = np.float32
# THESE ARE THE FOUR THINGS YOU SHOULD CHANGE
bintargetcount = 10  # number of walkers per bin
nbins = [10]  # You will have prod(binsperdim)+numberofdim*(2*splitIsolated) bins total
pcoordlength = 2  # length of the pcoord


class ODLDPropagator(WESTPropagator):
    def __init__(self, rc=None):
        super().__init__(rc)

        self.coord_len = pcoord_len
        self.coord_dtype = pcoord_dtype
        self.coord_ndim = 1

        self.initial_pcoord = np.array([(PI/4)], dtype=self.coord_dtype)

        self.sigma = 0.0001 ** (0.5)  # friction coefficient

        self.A = 2
        self.B = 20
        self.C = 0

        # Implement a reflecting boundary at this x value
        # (or None, for no reflection)
        self.reflect_at = PI
        self.reflect_zero = 0.0

    def get_pcoord(self, state):
        """Get the progress coordinate of the given basis or initial state."""
        state.pcoord = self.initial_pcoord.copy()

    def gen_istate(self, basis_state, initial_state):
        initial_state.pcoord = self.initial_pcoord.copy()
        initial_state.istate_status = initial_state.ISTATE_STATUS_PREPARED
        return initial_state

    def propagate(self, segments):

        A, B, C = self.A, self.B, self.C

        n_segs = len(segments)

        coords = np.empty(
            (n_segs, self.coord_len, self.coord_ndim), dtype=self.coord_dtype
        )

        for iseg, segment in enumerate(segments):
            coords[iseg, 0] = segment.pcoord[0]
       
        sigma = self.sigma
        gradfactor = self.sigma * self.sigma / 2
        coord_len = self.coord_len
        reflect_at = self.reflect_at
        reflect_zero = self.reflect_zero
        all_displacements = np.zeros(
            (n_segs, self.coord_len, self.coord_ndim), dtype=self.coord_dtype
        )
        for istep in range(1, coord_len):
            x = coords[:, istep - 1, :]

            all_displacements[:, istep, 0] = displacements = random_normal(
                scale=sigma, size=(n_segs,)
            )
            grad = 2 * B * sin(x) * cos(x) - 2 * ((A**2)-0.25)*(1/tan(x))* (1/(sin(x))**2)

            newx = x - gradfactor * grad + displacements

            if reflect_at is not None:
                # Anything that has moved beyond reflect_at must move back that much

                # boolean array of what to reflect
                to_reflect = newx > reflect_at

                # how far the things to reflect are beyond our boundary
                reflect_by = newx[to_reflect] - reflect_at

                # subtract twice how far they exceed the boundary by
                # puts them the same distance from the boundary, on the other side
                newx[to_reflect] -= 2 * reflect_by
                #newx[to_reflect] = (PI/4)
            if reflect_zero is not None:
                # Anything that has moved beyond reflect_at must move back that much

                # boolean array of what to reflect
                to_reflect = newx > reflect_zero

                # how far the things to reflect are beyond our boundary
                reflect_by = newx[to_reflect] - reflect_zero

                # subtract twice how far they exceed the boundary by
                # puts them the same distance from the boundary, on the other side
                newx[to_reflect] -= 2 * reflect_zero
                #newx[to_reflect] = (PI/4)

            coords[:, istep, :] = newx

        for iseg, segment in enumerate(segments):
            segment.pcoord[...] = coords[iseg, :]
            segment.data["displacement"] = all_displacements[iseg]
            segment.status = segment.SEG_STATUS_COMPLETE

        return segments
