# -*- coding: utf-8 -*-
"""
model_100_basicSt.py: models discharge and erosion across a topographic
surface assuming (1) stochastic Poisson storm arrivals, (2) single-direction
flow routing, and (3) Hortonian infiltration model. Includes stream-power
erosion plus linear diffusion.

Model 100 BasicSt

The hydrology uses calculation of drainage area using the standard "D8"
approach (assuming the input grid is a raster; "DN" if not), then modifies it
by running a lake-filling component. It then performs one of two options,
depending on the user's choice of "opt_stochastic_duration" (True or False).

If the user requests stochastic duration, the model iterates through a sequence
of storm and interstorm periods. Storm depth is drawn at random from a gamma
distribution, and storm duration from an exponential distribution; storm
intensity is then depth divided by duration. This sequencing is implemented by
overriding the run_for method.

If the user does not request stochastic duration (indicated by setting
opt_stochastic_duration to False), then the default (erosion_model base class)
run_for method is used. Whenever run_one_step is called, storm intensity is
generated at random from an exponential distribution with mean given by the
parameter daily_rainfall__mean_intensity. The stream power component is run for only a
fraction of the time step duration dt, as specified by the parameter
daily_rainfall_intermittency_factor. For example, if dt is 10 years and the intermittency
factor is 0.25, then the stream power component is run for only 2.5 years.

In either case, given a storm precipitation intensity :math:`P`, the runoff
production rate :math:`R` [L/T] is calculated using:

.. math::
    R = P - I (1 - \exp ( -P / I ))

where :math:`I` is the soil infiltration capacity. At the sub-grid scale, soil
infiltration capacity is assumed to have an exponential distribution of which
$I$ is the mean. Hence, there are always some spots within any given grid cell
that will generate runoff. This approach yields a smooth transition from
near-zero runoff (when :math:`I>>P`) to :math:`R \approx P` (when :math`P>>I`),
without a "hard threshold."
"""

import sys
import numpy as np

from landlab.components import LinearDiffuser, FastscapeEroder
from terrainbento.base_class import StochasticErosionModel


class BasicSt(StochasticErosionModel):
    """
    A StochasticHortonianSPModel generates a random sequency of
    runoff events across a topographic surface, calculating the resulting
    water discharge at each node.
    """

    def __init__(self, input_file=None, params=None,
                 BoundaryHandlers=None, OutputWriters=None):
        """Initialize the StochasticDischargeHortonianModel."""

        # Call ErosionModel's init
        super(BasicSt, self).__init__(input_file=input_file,
                                      params=params,
                                      BoundaryHandlers=BoundaryHandlers,
                                        OutputWriters=OutputWriters)

        # Get Parameters:
        K_sp = self.get_parameter_from_exponent('K_stochastic_sp', raise_error=False)
        K_ss = self.get_parameter_from_exponent('K_stochastic_ss', raise_error=False)
        linear_diffusivity = (self._length_factor**2.)*self.get_parameter_from_exponent('linear_diffusivity') # has units length^2/time

        # check that a stream power and a shear stress parameter have not both been given
        if K_sp != None and K_ss != None:
            raise ValueError('A parameter for both K_sp and K_ss has been'
                             'provided. Only one of these may be provided')
        elif K_sp != None or K_ss != None:
            if K_sp!= None:
                K = K_sp
            else:
                K = (self._length_factor**(1./2.))*K_ss # K_stochastic has units Lengtg^(1/2) per Time^(1/2_
        else:
            raise ValueError('A value for K_sp or K_ss  must be provided.')

        # instantiate rain generator
        self.instantiate_rain_generator()

        # Add a field for discharge
        if 'surface_water__discharge' not in self.grid.at_node:
            self.grid.add_zeros('node', 'surface_water__discharge')
        self.discharge = self.grid.at_node['surface_water__discharge']

        # Get the infiltration-capacity parameter
        infiltration_capacity = (self._length_factor)*self.params['infiltration_capacity']# has units length per time
        self.infilt = infiltration_capacity

        # Keep a reference to drainage area
        self.area = self.grid.at_node['drainage_area']

        # Run flow routing and lake filler
        self.flow_accumulator.run_one_step()

        # Instantiate a FastscapeEroder component
        self.eroder = FastscapeEroder(self.grid,
                                      K_sp=K,
                                      m_sp=self.params['m_sp'],
                                      n_sp=self.params['n_sp'])

        # Instantiate a LinearDiffuser component
        self.diffuser = LinearDiffuser(self.grid,
                                       linear_diffusivity=linear_diffusivity)


    def calc_runoff_and_discharge(self):
        """Calculate runoff rate and discharge; return runoff."""
        if self.rain_rate > 0.0 and self.infilt > 0.0:
            runoff = self.rain_rate - (self.infilt *
                                       (1.0 -
                                        np.exp(-self.rain_rate / self.infilt)))
            if runoff < 0:
                runoff = 0
        else:
            runoff = self.rain_rate
        self.discharge[:] = runoff * self.area
        return runoff


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

        # Handle water erosion
        self.handle_water_erosion(dt, flooded)

        # Do some soil creep
        self.diffuser.run_one_step(dt)

        # Finalize the run_one_step_method
        self.finalize_run_one_step(dt)


def main():
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print('Must include input file name on command line')
        sys.exit(1)

    em = BasicSt(input_file=infile)
    em.run()


if __name__ == '__main__':
    main()
