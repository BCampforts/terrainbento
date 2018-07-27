# coding: utf8
#! /usr/env/python

import os
import numpy as np

from numpy.testing import assert_array_equal, assert_array_almost_equal


from terrainbento.base_class import TwoLithologyErosionModel

_TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

file_name = os.path.join(_TEST_DATA_DIR, "example_for_weight.asc")


def test_no_contact_zone_width():

    params = {
        "model_grid": "RasterModelGrid",
        "dt": 1,
        "output_interval": 2.,
        "run_duration": 200.,
        "number_of_node_rows": 6,
        "number_of_node_columns": 9,
        "node_spacing": 10.0,
        "regolith_transport_parameter": 0.001,
        "water_erodability~lower": 0.001,
        "water_erodability~upper": 0.01,
        "contact_zone__width": 0,
        "lithology_contact_elevation__file_name": file_name,
        "m_sp": 0.5,
        "n_sp": 1.0,
    }

    model = TwoLithologyErosionModel(params=params)
    model._setup_rock_and_till()

    truth = np.ones(model.grid.size("node"))
    truth[model.grid.core_nodes[14:]] = 0.0

    assert_array_equal(model.erody_wt, truth)


def test_contact_zone_width():
    params = {
        "model_grid": "RasterModelGrid",
        "dt": 1,
        "output_interval": 2.,
        "run_duration": 200.,
        "number_of_node_rows": 6,
        "number_of_node_columns": 9,
        "node_spacing": 10.0,
        "regolith_transport_parameter": 0.001,
        "water_erodability~lower": 0.001,
        "water_erodability~upper": 0.01,
        "contact_zone__width": 10.,
        "lithology_contact_elevation__file_name": file_name,
        "m_sp": 0.5,
        "n_sp": 1.0,
    }

    model = TwoLithologyErosionModel(params=params)
    model._setup_rock_and_till()

    truth = np.array(
        [
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.,
            0.,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.95257413,
            0.,
            0.,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.,
            0.,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.26894142,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
            0.,
        ]
    )

    assert_array_almost_equal(model.erody_wt, truth)