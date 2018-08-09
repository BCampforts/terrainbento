# coding: utf8
#! /usr/env/python
"""terrainbento **BasicChRtTh** model program.

Erosion model program using non-linear diffusion, stream power with stream power
with a smoothed threshold and spatially varying erodability based on two bedrock
units, and discharge proportional to drainage area.

Landlab components used:
    1. `FlowAccumulator <http://landlab.readthedocs.io/en/release/landlab.components.flow_accum.html>`_
    2. `DepressionFinderAndRouter <http://landlab.readthedocs.io/en/release/landlab.components.flow_routing.html#module-landlab.components.flow_routing.lake_mapper>`_ (optional)
    3. `StreamPowerSmoothThresholdEroder <http://landlab.readthedocs.io/en/release/landlab.components.stream_power.html>`_
    4. `TaylorNonLinearDiffuser <http://landlab.readthedocs.io/en/release/landlab.components.taylor_nonlinear_hillslope_flux.html>`_
"""

import numpy as np

from landlab.components import StreamPowerSmoothThresholdEroder, TaylorNonLinearDiffuser
from terrainbento.base_class import TwoLithologyErosionModel


class BasicChRtTh(TwoLithologyErosionModel):
    """**BasicChRtTh** model program.

    **BasicChRtTh** combines the **BasicCh**, **BasicTh** and **BasicRt**
    programs by allowing for two lithologies, an "upper" layer and a "lower"
    layer, permitting the use of an smooth erosion threshold for each lithology,
    and using non-linear hillslope transport. Given a spatially varying contact
    zone elevation, :math:`\eta_C(x,y))`, model **BasicChRtTh** evolves a
    topographic surface described by :math:`\eta` with the following governing equations:


    .. math::

        \\frac{\partial \eta}{\partial t} = -\left[\omega - \omega_c (1 - e^{-\omega /\omega_c}) \\right]  - \\nabla q_h

        \omega = K(\eta, \eta_C) A^{m} S^{n}

        K(\eta, \eta_C ) = w K_1 + (1 - w) K_2,

        \omega_c(\eta, \eta_C ) = w \omega_{c1} + (1 - w) \omega_{c2}

        w = \\frac{1}{1+\exp \left( -\\frac{(\eta -\eta_C )}{W_c}\\right)}

        q_h = -DS \left[ 1 + \left( \\frac{S}{S_c} \\right)^2 +  \left( \\frac{S}{S_c} \\right)^4 + ... \left( \\frac{S}{S_c} \\right)^{2(N-1)} \\right]


    where :math:`A` is the local drainage area, :math:`S` is the local slope,
    :math:`m` and :math:`n` are the drainage area and slope exponent parameters,
    :math:`W_c` is the contact-zone width, :math:`K_1` and :math:`K_2` are the
    erodabilities of the upper and lower lithologies, and :math:`D` is the
    regolith transport parameter. :math:`w` is a weight used to calculate the
    effective erodability :math:`K(\eta, \eta_C)` based on the depth to the
    contact zone and the width of the contact zone. :math:`N` is the number of
    terms in the Taylor Series expansion. Presently :math:`N` is set at 11 and
    is not a user defined parameter.

    The weight :math:`w` promotes smoothness in the solution of erodability at a
    given point. When the surface elevation is at the contact elevation, the
    erodability is the average of :math:`K_1` and :math:`K_2`; above and below
    the contact, the erodability approaches the value of :math:`K_1` and :math:`K_2`
    at a rate related to the contact zone width. Thus, to make a very sharp
    transition, use a small value for the contact zone width.

    The **BasicChRtTh** program inherits from the terrainbento
    **TwoLithologyErosionModel** base class. In addition to the parameters
    required by the base class, models built with this program require the
    following parameters.

    +--------------------+-----------------------------------------+
    | Parameter Symbol   | Input File Parameter Name               |
    +====================+=========================================+
    |:math:`m`           | ``m_sp``                                |
    +--------------------+-----------------------------------------+
    |:math:`n`           | ``n_sp``                                |
    +--------------------+-----------------------------------------+
    |:math:`K_{1}`       | ``water_erodability~upper``             |
    +--------------------+-----------------------------------------+
    |:math:`K_{2}`       | ``water_erodability~lower``             |
    +--------------------+-----------------------------------------+
    |:math:`\omega_{c1}` | ``water_erosion_rule~upper__threshold`` |
    +--------------------+-----------------------------------------+
    |:math:`\omega_{c2}` | ``water_erosion_rule~lower__threshold`` |
    +--------------------+-----------------------------------------+
    |:math:`W_{c}`       | ``contact_zone__width``                 |
    +--------------------+-----------------------------------------+
    |:math:`D`           | ``regolith_transport_parameter``        |
    +--------------------+-----------------------------------------+
    |:math:`S_c`         | ``critical_slope``                      |
    +--------------------+-----------------------------------------+

    Refer to the terrainbento manuscript Table 5 (URL to manuscript when
    published) for full list of parameter symbols, names, and dimensions.

    *Specifying the Lithology Contact*

    In all two-lithology models the spatially variable elevation of the contact
    elevation must be given as the file path to an ESRII ASCII format file using
    the parameter ``lithology_contact_elevation__file_name``. If topography was
    created using an input DEM, then the shape of the field contained in the
    file must be the same as the input DEM. If synthetic topography is used then
    the shape of the field must be ``number_of_node_rows-2`` by
    ``number_of_node_columns-2``. This is because the read-in DEM will be padded
    by a halo of size 1.

    *Reference Frame Considerations*

    Note that the developers had to make a decision about how to represent the
    contact. We could represent the contact between two layers either as a depth
    below present land surface, or as an altitude. Using a depth would allow for
    vertical motion, because for a fixed surface, the depth remains constant
    while the altitude changes. But the depth must be updated every time the
    surface is eroded or aggrades. Using an altitude avoids having to update the
    contact position every time the surface erodes or aggrades, but any tectonic
    motion would need to be applied to the contact position as well. We chose to
    use the altitude approach because this model was originally written for an
    application with lots of erosion expected but no tectonics.

    If implementing tectonics is desired, consider using either the
    **SingleNodeBaselevelHandler** or the **NotCoreNodeBaselevelHandler** which
    modify both the ``topographic__elevation`` and the ``bedrock__elevation``
    fields.

    """

    def __init__(self, input_file=None, params=None, OutputWriters=None):
        """
        Parameters
        ----------
        input_file : str
            Path to model input file. See wiki for discussion of input file
            formatting. One of input_file or params is required.
        params : dict
            Dictionary containing the input file. One of input_file or params is
            required.
        OutputWriters : class, function, or list of classes and/or functions, optional
            Classes or functions used to write incremental output (e.g. make a
            diagnostic plot).

        Returns
        -------
        BasicChRtTh : model object

        Examples
        --------
        This is a minimal example to demonstrate how to construct an instance
        of model **BasicChRtCh**. Note that a YAML input file can be used instead of
        a parameter dictionary. For more detailed examples, including steady-
        state test examples, see the terrainbento tutorials.

        To begin, import the model class.

        >>> from terrainbento import BasicChRtTh

        Set up a parameters variable.

        >>> params = {"model_grid": "RasterModelGrid",
        ...           "dt": 1,
        ...           "output_interval": 2.,
        ...           "run_duration": 200.,
        ...           "number_of_node_rows" : 6,
        ...           "number_of_node_columns" : 9,
        ...           "node_spacing" : 10.0,
        ...           "regolith_transport_parameter": 0.001,
        ...           "water_erodability~lower": 0.001,
        ...           "water_erodability~upper": 0.01,
        ...           "water_erosion_rule~upper__threshold": 0.1,
        ...           "water_erosion_rule~lower__threshold": 0.2,
        ...           "contact_zone__width": 1.0,
        ...           "lithology_contact_elevation__file_name": "tests/data/example_contact_elevation.asc",
        ...           "m_sp": 0.5,
        ...           "n_sp": 1.0,
        ...           "critical_slope": 0.1}

        Construct the model.

        >>> model = BasicChRtTh(params=params)

        Running the model with ``model.run()`` would create output, so here we
        will just run it one step.

        >>> model.run_one_step(1.)
        >>> model.model_time
        1.0

        """
        # Call ErosionModel"s init
        super(BasicChRtTh, self).__init__(
            input_file=input_file, params=params, OutputWriters=OutputWriters
        )

        # Save the threshold values for rock and till
        self.rock_thresh = self.get_parameter_from_exponent(
            "water_erosion_rule~lower__threshold"
        )
        self.till_thresh = self.get_parameter_from_exponent(
            "water_erosion_rule~upper__threshold"
        )

        # Set up rock-till boundary and associated grid fields.
        self._setup_rock_and_till_with_threshold()

        # Instantiate a StreamPowerSmoothThresholdEroder component
        self.eroder = StreamPowerSmoothThresholdEroder(
            self.grid,
            K_sp=self.erody,
            threshold_sp=self.threshold,
            m_sp=self.m,
            n_sp=self.n,
        )

        # Instantiate a LinearDiffuser component
        self.diffuser = TaylorNonLinearDiffuser(
            self.grid,
            linear_diffusivity=self.regolith_transport_parameter,
            slope_crit=self.params["critical_slope"],
            nterms=7,
        )

    def run_one_step(self, dt):
        """Advance model **BasicChRtTh** for one time-step of duration dt.

        The **run_one_step** method does the following:

        1. Directs flow and accumulates drainage area.

        2. Assesses the location, if any, of flooded nodes where erosion should
           not occur.

        3. Assesses if a **PrecipChanger** is an active BoundaryHandler and if
           so, uses it to modify the two erodability by water values.

        4. Updates the spatially variable erodability and threshold values based
           on the relative distance between the topographic surface and the lithology
           contact.

        5. Calculates detachment-limited erosion by water.

        6. Calculates topographic change by non-linear diffusion.

        7. Finalizes the step using the **ErosionModel** base class function
           **finalize__run_one_step**. This function updates all BoundaryHandlers
           by ``dt`` and increments model time by ``dt``.

        Parameters
        ----------
        dt : float
            Increment of time for which the model is run.
        """
        # Direct and accumulate flow
        self.flow_accumulator.run_one_step()

        # Get IDs of flooded nodes, if any
        if self.flow_accumulator.depression_finder is None:
            flooded = []
        else:
            flooded = np.where(
                self.flow_accumulator.depression_finder.flood_status == 3
            )[0]

        # Update the erodability and threshold field
        self._update_erodability_and_threshold_fields()

        # Do some erosion (but not on the flooded nodes)
        self.eroder.run_one_step(dt, flooded_nodes=flooded)

        # Do some soil creep
        self.diffuser.run_one_step(
            dt, dynamic_dt=True, if_unstable="raise", courant_factor=0.1
        )

        # Finalize the run_one_step_method
        self.finalize__run_one_step(dt)


def main():  # pragma: no cover
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print("Must include input file name on command line")
        sys.exit(1)

    chrt = BasicChRtTh(input_file=infile)
    chrt.run()


if __name__ == "__main__":
    main()