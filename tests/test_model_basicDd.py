# coding: utf8
# !/usr/env/python

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal  # assert_array_equal,

from terrainbento import BasicDd
from terrainbento.utilities import filecmp


def test_bad_n_sp(clock_simple):
    params = {
        "model_grid": "RasterModelGrid",
        "clock": clock_simple,
        "water_erodability": 0.001,
        "n_sp": 1.01,
        "regolith_transport_parameter": 0.001,
        "water_erosion_rule__threshold": 0.001,
        "water_erosion_rule__thresh_depth_derivative": 0.001,
    }

    with pytest.raises(ValueError):
        BasicDd(params=params)


# def test_steady_Ksp_no_precip_changer_no_thresh():
#     U = 0.0001
#     K = 0.001
#     m = 0.5
#     n = 1.0
#     step = 1000
#     threshold = 0.0
#     thresh_change_per_depth = 0.0
#     # construct dictionary. note that D is turned off here
#     params = {"model_grid": "RasterModelGrid",
#               "clock": {"step": 1,
#               "output_interval": 2.,
#               "stop": 200.},
#               "number_of_node_rows" : 3,
#               "number_of_node_columns" : 20,
#               "node_spacing" : 100.0,
#               "north_boundary_closed": True,
#               "south_boundary_closed": True,
#               "regolith_transport_parameter": 0.,
#               "water_erodability": K,
#               "m_sp": m,
#               "n_sp": n,
#               "water_erosion_rule__threshold": threshold,
#               "water_erosion_rule__thresh_depth_derivative": thresh_change_per_depth,
#               "random_seed": 3141,
#               "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
#               "NotCoreNodeBaselevelHandler": {"modify_core_nodes": True,
#                                               "lowering_rate": -U}}
#
#     # construct and run model
#     model = BasicDd(params=params)
#     for _ in range(100):
#         model.run_one_step(step)
#
#     # construct actual and predicted slopes
#     actual_slopes = model.grid.at_node["topographic__steepest_slope"]
#     actual_areas = model.grid.at_node["drainage_area"]
#     predicted_slopes = ((U/K + threshold)/((actual_areas**m))) ** (1./n)
#
#     # assert actual and predicted slopes are the same.
#     assert_array_almost_equal(actual_slopes[model.grid.core_nodes[1:-1]],
#                               predicted_slopes[model.grid.core_nodes[1:-1]])


def test_steady_Ksp_no_precip_changer_no_thresh_change(clock_simple):
    U = 0.0001
    K = 0.001
    m = 0.5
    n = 1.0
    step = 1000
    threshold = 0.1
    thresh_change_per_depth = 0.0
    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": clock_simple,
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "water_erosion_rule__thresh_depth_derivative": thresh_change_per_depth,
        "random_seed": 3141,
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {
            "modify_core_nodes": True,
            "lowering_rate": -U,
        },
    }

    # construct and run model
    model = BasicDd(params=params)
    for _ in range(200):
        model.run_one_step(step)

    # construct actual and predicted slopes
    # note that since we have a smooth threshold, we do not have a true
    # analytical solution, but a bracket within wich we expect the actual
    # slopes to fall.
    actual_slopes = model.grid.at_node["topographic__steepest_slope"]
    actual_areas = model.grid.at_node["drainage_area"]
    predicted_slopes_upper = ((U + threshold) / (K * (actual_areas ** m))) ** (
        1. / n
    )
    predicted_slopes_lower = ((U + 0.0) / (K * (actual_areas ** m))) ** (
        1. / n
    )

    # assert actual and predicted slopes are in the correct range for the
    # slopes.
    assert np.all(
        actual_slopes[model.grid.core_nodes[1:-1]]
        > predicted_slopes_lower[model.grid.core_nodes[1:-1]]
    )

    assert np.all(
        actual_slopes[model.grid.core_nodes[1:-1]]
        < predicted_slopes_upper[model.grid.core_nodes[1:-1]]
    )


def test_steady_Ksp_no_precip_changer_with_thresh_change(clock_simple):
    U = 0.0001
    K = 0.001
    m = 0.5
    n = 1.0
    step = 1000
    threshold = 0.1
    thresh_change_per_depth = 0.001
    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": clock_simple,
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "water_erosion_rule__thresh_depth_derivative": thresh_change_per_depth,
        "random_seed": 3141,
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {
            "modify_core_nodes": True,
            "lowering_rate": -U,
        },
    }

    # construct and run model
    model = BasicDd(params=params)
    for _ in range(200):
        model.run_one_step(step)

    # construct actual and predicted slopes
    # note that since we have a smooth threshold, we do not have a true
    # analytical solution, but a bracket within wich we expect the actual
    # slopes to fall.
    # and with the threshold changing, we can only expect that the slopes are
    # steeper than the lower bound.
    actual_slopes = model.grid.at_node["topographic__steepest_slope"]
    actual_areas = model.grid.at_node["drainage_area"]
    predicted_slopes_lower = ((U + 0.0) / (K * (actual_areas ** m))) ** (
        1. / n
    )

    # assert actual and predicted slopes are in the correct range for the
    # slopes.
    assert np.all(
        actual_slopes[model.grid.core_nodes[1:-1]]
        > predicted_slopes_lower[model.grid.core_nodes[1:-1]]
    )


def test_steady_Ksp_no_precip_changer(clock_simple):
    U = 0.0001
    K = 0.001
    m = 0.5
    n = 1.0
    step = 1000
    threshold = 0.000001
    thresh_change_per_depth = 0
    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": clock_simple,
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "water_erosion_rule__thresh_depth_derivative": thresh_change_per_depth,
        "random_seed": 3141,
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {
            "modify_core_nodes": True,
            "lowering_rate": -U,
        },
    }

    # construct and run model
    model = BasicDd(params=params)
    for _ in range(100):
        model.run_one_step(step)

    # construct actual and predicted slopes
    actual_slopes = model.grid.at_node["topographic__steepest_slope"]
    actual_areas = model.grid.at_node["drainage_area"]
    predicted_slopes = ((U / K + threshold) / ((actual_areas ** m))) ** (
        1. / n
    )

    # assert actual and predicted slopes are the same.
    assert_array_almost_equal(
        actual_slopes[model.grid.core_nodes[1:-1]],
        predicted_slopes[model.grid.core_nodes[1:-1]],
        decimal=4,
    )


def test_steady_Ksp_no_precip_changer_with_depression_finding(clock_simple):
    U = 0.0001
    K = 0.001
    m = 0.5
    n = 1.0
    step = 1000
    threshold = 0.000001
    thresh_change_per_depth = 0
    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": clock_simple,
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "water_erosion_rule__thresh_depth_derivative": thresh_change_per_depth,
        "random_seed": 3141,
        "depression_finder": "DepressionFinderAndRouter",
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {
            "modify_core_nodes": True,
            "lowering_rate": -U,
        },
    }

    # construct and run model
    model = BasicDd(params=params)
    for _ in range(100):
        model.run_one_step(step)

    # construct actual and predicted slopes
    actual_slopes = model.grid.at_node["topographic__steepest_slope"]
    actual_areas = model.grid.at_node["drainage_area"]
    predicted_slopes = ((U / K + threshold) / ((actual_areas ** m))) ** (
        1. / n
    )

    # assert actual and predicted slopes are the same.
    assert_array_almost_equal(
        actual_slopes[model.grid.core_nodes[1:-1]],
        predicted_slopes[model.grid.core_nodes[1:-1]],
        decimal=4,
    )


def test_with_precip_changer(clock_simple, precip_defaults, precip_testing_factor):
    K = 0.01
    threshold = 0.000001
    thresh_change_per_depth = 0
    params = {
        "model_grid": "RasterModelGrid",
        "clock": clock_simple,
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "south_boundary_closed": True,
        "regolith_transport_parameter": 0.,
        "water_erodability": K,
        "m_sp": 0.5,
        "n_sp": 1.0,
        "water_erosion_rule__threshold": threshold,
        "water_erosion_rule__thresh_depth_derivative": thresh_change_per_depth,
        "random_seed": 3141,
        "BoundaryHandlers": "PrecipChanger",
        "PrecipChanger": precip_defaults,
    }

    model = BasicDd(params=params)
    assert model.eroder.K == K
    assert "PrecipChanger" in model.boundary_handler
    model.run_one_step(1.0)
    model.run_one_step(1.0)
    assert round(model.eroder.K, 5) == round(K * precip_testing_factor, 5)


def test_diffusion_only(clock_simple):
    total_time = 5.0e6
    U = 0.001
    D = 1
    m = 0.75
    n = 1.0
    step = 1000
    threshold = 0.01
    thresh_change_per_depth = 0

    # construct dictionary. note that D is turned off here
    params = {
        "model_grid": "RasterModelGrid",
        "clock": clock_simple,
        "number_of_node_rows": 3,
        "number_of_node_columns": 21,
        "node_spacing": 100.0,
        "north_boundary_closed": True,
        "west_boundary_closed": False,
        "south_boundary_closed": True,
        "regolith_transport_parameter": D,
        "water_erodability": 0.0,
        "m_sp": m,
        "n_sp": n,
        "water_erosion_rule__threshold": threshold,
        "water_erosion_rule__thresh_depth_derivative": thresh_change_per_depth,
        "random_seed": 3141,
        "BoundaryHandlers": "NotCoreNodeBaselevelHandler",
        "NotCoreNodeBaselevelHandler": {
            "modify_core_nodes": True,
            "lowering_rate": -U,
        },
    }
    nts = int(total_time / step)

    reference_node = 9
    # construct and run model
    model = BasicDd(params=params)
    for _ in range(nts):
        model.run_one_step(step)

    predicted_z = model.z[model.grid.core_nodes[reference_node]] - (
        U / (2. * D)
    ) * (
        (
            model.grid.x_of_node
            - model.grid.x_of_node[model.grid.core_nodes[reference_node]]
        )
        ** 2
    )

    # assert actual and predicted elevations are the same.
    assert_array_almost_equal(
        predicted_z[model.grid.core_nodes],
        model.z[model.grid.core_nodes],
        decimal=2,
    )

    # assert actual and predicted elevations are the same.
    assert_array_almost_equal(
        predicted_z[model.grid.core_nodes],
        model.z[model.grid.core_nodes],
        decimal=2,
    )
