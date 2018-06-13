# -*- coding: utf-8 -*-
"""
model_018_basicDdHy.py: erosion model with hybrid alluvium and a threshold
that varies with cumulative incision depth.

Landlab components used: FlowRouter, DepressionFinderAndRouter,
LinearDiffuser, and HybridAlluvium

"""
import sys
import numpy as np

from landlab.components import LinearDiffuser, ErosionDeposition
from terrainbento.base_class import ErosionModel


class BasicDdHy(ErosionModel):
    """
    A BasicDdHy computes erosion using 1) the hybrid alluvium component
    with a threshold that varies with cumulative incision depth, the linear
    diffusion component.
    """

    def __init__(self, input_file=None, params=None, BoundaryHandlers=None, OutputWriters=None):
        """
        Initialize the BasicDdHy
        """

        # Call ErosionModel's init
        super(BasicDdHy, self).__init__(input_file=input_file,
                                        params=params,
                                        BoundaryHandlers=BoundaryHandlers,
                                        OutputWriters=OutputWriters)

        # Get Parameters and convert units if necessary:
        self.K_sp = self.get_parameter_from_exponent('water_erodability')
        regolith_transport_parameter = ((self._length_factor ** 2)  # L2/T
                * self.get_parameter_from_exponent('regolith_transport_parameter'))
        v_s = self.get_parameter_from_exponent('v_sc') # unitless
        self.sp_crit = (self._length_factor  # L/T
                * self.get_parameter_from_exponent('erosion__threshold'))

        # Create a field for the (initial) erosion threshold
        self.threshold = self.grid.add_zeros('node', 'erosion__threshold')
        self.threshold[:] = self.sp_crit  #starting value

        # Handle solver option
        try:
            solver = self.params['solver']
        except:
            solver = 'original'

        # Instantiate an ErosionDeposition component
        self.eroder = ErosionDeposition(self.grid,
                            K=self.K_sp,
                            F_f=self.params['F_f'],
                            phi=self.params['phi'],
                            v_s=v_s,
                            m_sp=self.params['m_sp'],
                            n_sp=self.params['n_sp'],
                            sp_crit='erosion__threshold',
                            method='threshold_stream_power',
                            discharge_method='drainage_area',
                            area_field='drainage_area',
                            solver=solver)

        # Get the parameter for rate of threshold increase with erosion depth
        self.thresh_change_per_depth = self.params['thresh_change_per_depth']

        # Instantiate a LinearDiffuser component
        self.diffuser = LinearDiffuser(self.grid,
                                       linear_diffusivity=regolith_transport_parameter)

    def run_one_step(self, dt):
        """
        Advance model for one time-step of duration dt.
        """

        # Route flow
        self.flow_accumulator.run_one_step()

        # Get IDs of flooded nodes, if any
        if self.flow_accumulator.depression_finder is None:
            flooded = []
        else:
            flooded = np.where(self.flow_accumulator.depression_finder.flood_status==3)[0]

        # Calculate cumulative erosion and update threshold
        cum_ero = self.grid.at_node['cumulative_erosion__depth']
        cum_ero[:] = (self.z
                     - self.grid.at_node['initial_topographic__elevation'])
        self.threshold[:] = (self.sp_crit
                             - (self.thresh_change_per_depth * cum_ero))
        self.threshold[self.threshold < self.sp_crit] = self.sp_crit

        # Do some erosion (but not on the flooded nodes)
        # (if we're varying K through time, update that first)
        if 'PrecipChanger' in self.boundary_handler:
            self.eroder.K = (self.K_sp
                             * self.boundary_handler['PrecipChanger'].get_erodibility_adjustment_factor())
        self.eroder.run_one_step(dt, flooded_nodes=flooded)

        # Do some soil creep
        self.diffuser.run_one_step(dt)

        # Finalize the run_one_step_method
        self.finalize__run_one_step(dt)


def main():
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print('Must include input file name on command line')
        sys.exit(1)

    em = BasicDdHy(input_file=infile)
    em.run()


if __name__ == '__main__':
    main()