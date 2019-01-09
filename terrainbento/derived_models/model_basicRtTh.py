# coding: utf8
# !/usr/env/python
"""terrainbento **BasicRtTh** model program.

Erosion model program using linear diffusion, stream power with a smoothed
threshold and spatially varying erodability based on two bedrock units, and
discharge proportional to drainage area.

Landlab components used:
    1. `FlowAccumulator <http://landlab.readthedocs.io/en/release/landlab.components.flow_accum.html>`_
    2. `DepressionFinderAndRouter <http://landlab.readthedocs.io/en/release/landlab.components.flow_routing.html#module-landlab.components.flow_routing.lake_mapper>`_ (optional)
    3. `StreamPowerSmoothThresholdEroder <http://landlab.readthedocs.io/en/release/landlab.components.stream_power.html>`_
    4. `LinearDiffuser <http://landlab.readthedocs.io/en/release/landlab.components.diffusion.html>`_
"""

import numpy as np

from landlab.components import LinearDiffuser, StreamPowerSmoothThresholdEroder
from terrainbento.base_class import TwoLithologyErosionModel

_REQUIRED_FIELDS = ["topographic__elevation"]


class BasicRtTh(TwoLithologyErosionModel):
    r"""**BasicRtTh** model program.

    **BasicRtTh** is a model program that combines the **BasicRt** and
    **BasicTh** programs by allowing for two lithologies, an "upper" layer and a
    "lower" layer, and permitting the use of an smooth erosion threshold for
    each lithology. Given a spatially varying contact zone elevation,
    :math:`\eta_C(x,y))`, model **BasicRtTh** evolves a topographic surface
    described by :math:`\eta` with the following governing equations:

    .. math::

        \\frac{\partial \eta}{\partial t} = -\left[\omega - \omega_c (1 - e^{-\omega /\omega_c}) \\right]  + D\\nabla^2 \eta

        \omega = K(\eta, \eta_C) A^{m} S^{n}

        K(\eta, \eta_C ) = w K_1 + (1 - w) K_2,

        \omega_c(\eta, \eta_C ) = w \omega_{c1} + (1 - w) \omega_{c2}

        w = \\frac{1}{1+\exp \left( -\\frac{(\eta -\eta_C )}{W_c}\\right)}


    where :math:`A` is the local drainage area, :math:`S` is the local slope,
    :math:`m` and :math:`n` are the drainage area and slope exponent parameters,
    :math:`W_c` is the contact-zone width, :math:`K_1` and :math:`K_2` are the
    erodabilities of the upper and lower lithologies, :math:`\omega_{c1}` and
    :math:`\omega_{c2}` are the erosion thresholds of the upper and lower
    lithologies, and :math:`D` is the regolith transport parameter. :math:`w` is
    a weight used to calculate the effective erodability :math:`K(\eta, \eta_C)`
    based on the depth to the contact zone and the width of the contact zone.
    :math:`\omega` is the erosion rate that would be calculated without the use
    of a threshold and as the threshold increases the erosion rate smoothly
    transitions between zero and :math:`\omega`.

    The weight :math:`w` promotes smoothness in the solution of erodability at a
    given point. When the surface elevation is at the contact elevation, the
    erodability is the average of :math:`K_1` and :math:`K_2`; above and below
    the contact, the erodability approaches the value of :math:`K_1` and :math:`K_2`
    at a rate related to the contact zone width. Thus, to make a very sharp
    transition, use a small value for the contact zone width.

    The **BasicRtTh** program inherits from the terrainbento
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
    |:math:`K_{1}`       | ``water_erodability_upper``             |
    +--------------------+-----------------------------------------+
    |:math:`K_{2}`       | ``water_erodability_lower``             |
    +--------------------+-----------------------------------------+
    |:math:`\omega_{c1}` | ``water_erosion_rule_upper__threshold`` |
    +--------------------+-----------------------------------------+
    |:math:`\omega_{c2}` | ``water_erosion_rule_lower__threshold`` |
    +--------------------+-----------------------------------------+
    |:math:`W_{c}`       | ``contact_zone__width``                 |
    +--------------------+-----------------------------------------+
    |:math:`D`           | ``regolith_transport_parameter``        |
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

    def __init__(
        self,
        clock,
        grid,
        water_erosion_rule_upper__threshold=1.,
        water_erosion_rule_lower__threshold=1.,
        **kwargs
    ):
        """
        Parameters
        ----------


        Returns
        -------
        BasicRtTh : model object

        Examples
        --------
        This is a minimal example to demonstrate how to construct an instance
        of model **BasicRtTh**. For more detailed examples, including steady-state
        test examples, see the terrainbento tutorials.

        To begin, import the model class.

        >>> from landlab import RasterModelGrid
        >>> from landlab.values import random, constant
        >>> from terrainbento import Clock, BasicRtTh
        >>> clock = Clock(start=0, stop=100, step=1)
        >>> grid = RasterModelGrid((5,5))
        >>> _ = random(grid, "topographic__elevation")
        >>> _ = constant(grid, "lithology_contact__elevation", constant=-10.)

        Construct the model.

        >>> model = BasicRtTh(clock, grid)

        Running the model with ``model.run()`` would create output, so here we
        will just run it one step.

        >>> model.run_one_step(1.)
        >>> model.model_time
        1.0

        """
        # Call ErosionModel"s init
        super(BasicRtTh, self).__init__(clock, grid, **kwargs)

        if float(self.n) != 1.0:
            raise ValueError("Model only supports n equals 1.")

        # verify correct fields are present.
        self._verify_fields(_REQUIRED_FIELDS)

        # Save the threshold values for rock and till
        self.rock_thresh = water_erosion_rule_lower__threshold
        self.till_thresh = water_erosion_rule_upper__threshold

        # Set up rock-till boundary and associated grid fields.
        self._setup_rock_and_till_with_threshold()

        # Instantiate a StreamPowerSmoothThresholdEroder component
        self.eroder = StreamPowerSmoothThresholdEroder(
            self.grid,
            K_sp=self.erody,
            threshold_sp=self.threshold,
            m_sp=self.m,
            n_sp=self.n,
            use_Q="surface_water__discharge",
        )

        # Instantiate a LinearDiffuser component
        self.diffuser = LinearDiffuser(
            self.grid, linear_diffusivity=self.regolith_transport_parameter
        )

    def run_one_step(self, step):
        """Advance model **BasicRtTh** for one time-step of duration step.

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

        6. Calculates topographic change by linear diffusion.

        7. Finalizes the step using the **ErosionModel** base class function
           **finalize__run_one_step**. This function updates all BoundaryHandlers
           by ``step`` and increments model time by ``step``.

        Parameters
        ----------
        step : float
            Increment of time for which the model is run.
        """
        # create and move water
        self.create_and_move_water(step)

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
        self.eroder.run_one_step(step, flooded_nodes=flooded)

        # Do some soil creep
        self.diffuser.run_one_step(step)

        # Finalize the run_one_step_method
        self.finalize__run_one_step(step)


def main():  # pragma: no cover
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print("Must include input file name on command line")
        sys.exit(1)

    thrt = BasicRtTh(input_file=infile)
    thrt.run()


if __name__ == "__main__":
    main()
