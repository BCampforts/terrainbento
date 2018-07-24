# coding: utf8
#! /usr/env/python

import pytest
import numpy as np
from terrainbento import StochasticErosionModel, BasicSt


def test_defaults():
    params = {"dt": 1, "output_interval": 2., "run_duration": 200.}
    model = StochasticErosionModel(params=params)
    assert model.opt_stochastic_duration == False
    assert model.record_rain == False


def test_init_record_opt_true():
    params = {"dt": 1, "output_interval": 2., "run_duration": 200., "record_rain": True}
    model = StochasticErosionModel(params=params)
    assert model.record_rain == True
    assert isinstance(model.rain_record, dict)
    fields = ["event_start_time", "event_duration", "rainfall_rate", "runoff_rate"]
    for f in fields:
        assert f in model.rain_record
        assert len(model.rain_record[f]) == 0


def test_init_record_opt_false():
    params = {
        "dt": 1,
        "output_interval": 2.,
        "run_duration": 200.,
        "record_rain": False,
    }
    model = StochasticErosionModel(params=params)
    assert model.record_rain == False
    assert model.rain_record is None


def test_run_stochastic_opt_true():
    params = {
        "opt_stochastic_duration": True,
        "dt": 1,
        "output_interval": 2.,
        "run_duration": 200.,
        "record_rain": True,
        "m_sp": 0.5,
        "n_sp": 1.0,
        "water_erodability~stochastic": 0.01,
        "regolith_transport_parameter": 0.1,
        "infiltration_capacity": 0.0,
        "mean_storm_duration": 2.,
        "mean_interstorm_duration": 3.,
        "mean_storm_depth": 1.,
        "random_seed": 1234,
    }

    model = BasicSt(params=params)
    assert model.opt_stochastic_duration == True
    model.run_for(10, 10000.)

    rainfall_rate = np.asarray(model.rain_record["rainfall_rate"])
    event_duration = np.asarray(model.rain_record["event_duration"])

    dry_times = event_duration[rainfall_rate == 0]
    wet_times = event_duration[rainfall_rate > 0]

    np.testing.assert_almost_equal(
        np.mean(dry_times), params["mean_interstorm_duration"], decimal=1
    )
    np.testing.assert_almost_equal(
        np.mean(wet_times), params["mean_storm_duration"], decimal=1
    )

    avg_storm_depth = np.sum((rainfall_rate * event_duration)) / len(wet_times)

    np.testing.assert_array_almost_equal(
        avg_storm_depth, params["mean_storm_depth"], decimal=1
    )


def test_run_stochastic_opt_false():
    params = {
        "opt_stochastic_duration": False,
        "dt": 10,
        "output_interval": 2.,
        "run_duration": 200.,
        "record_rain": True,
        "m_sp": 0.5,
        "n_sp": 1.0,
        "water_erodability~stochastic": 0.01,
        "regolith_transport_parameter": 0.1,
        "infiltration_capacity": 0.0,
        "daily_rainfall__mean_intensity": 1.,
        "daily_rainfall_intermittency_factor": 0.1,
        "daily_rainfall__precipitation_shape_factor": 0.6,
        "number_of_sub_time_steps": 1,
        "random_seed": 1234,
    }

    model = BasicSt(params=params)
    assert model.opt_stochastic_duration == False
    model.run_for(params["dt"], 10000.)

    rainfall_rate = np.asarray(model.rain_record["rainfall_rate"])
    event_duration = np.asarray(model.rain_record["event_duration"])

    dry_times = event_duration[rainfall_rate == 0]
    wet_times = event_duration[rainfall_rate > 0]

    assert (
        np.array_equiv(
            dry_times,
            params["dt"] * (1. - params["daily_rainfall_intermittency_factor"]),
        )
        == True
    )
    assert (
        np.array_equiv(
            wet_times, params["dt"] * (params["daily_rainfall_intermittency_factor"])
        )
        == True
    )

    avg_storm_depth = np.sum((rainfall_rate * event_duration)) / len(wet_times)

    np.testing.assert_array_almost_equal(
        avg_storm_depth, params["daily_rainfall__mean_intensity"], decimal=1
    )


def test_freq_file_with_opt_duration_true():
    params = {
        "model_grid": "RasterModelGrid",
        "dt": 1,
        "output_interval": 2.,
        "run_duration": 200.,
        "number_of_node_rows": 3,
        "number_of_node_columns": 20,
        "node_spacing": 100.0,
        "random_seed": 3141,
        "frequency_filename": "yams.txt",
        "opt_stochastic_duration": True,
    }
    with pytest.raises(ValueError):
        _ = StochasticErosionModel(params=params)


def test_run_opt_true_with_changer():
    pass


def test_run_opt_false_with_changer():
    pass


def test_reset_random_seed_stochastic_duration_true():
    params = {
        "opt_stochastic_duration": True,
        "dt": 1,
        "output_interval": 2.,
        "run_duration": 200.,
        "record_rain": True,
        "m_sp": 0.5,
        "n_sp": 1.0,
        "water_erodability~stochastic": 0.01,
        "regolith_transport_parameter": 0.1,
        "infiltration_capacity": 0.0,
        "mean_storm_duration": 2.,
        "mean_interstorm_duration": 3.,
        "mean_storm_depth": 1.,
        "random_seed": 0,
    }

    model = BasicSt(params=params)
    dt = 1
    runtime = 200

    model.rain_generator.delta_t = dt
    model.rain_generator.run_time = runtime
    model.reset_random_seed()
    duration_1 = []
    precip_1 = []

    for (tr, p) in model.rain_generator.yield_storm_interstorm_duration_intensity():
        precip_1.append(p)
        duration_1.append(tr)

    model.rain_generator.delta_t = dt
    model.rain_generator.run_time = runtime
    model.reset_random_seed()

    duration_2 = []
    precip_2 = []

    for (tr, p) in model.rain_generator.yield_storm_interstorm_duration_intensity():
        precip_2.append(p)
        duration_2.append(tr)

    np.testing.assert_array_equal(duration_1, duration_2)
    np.testing.assert_array_equal(precip_1, precip_2)


def test_reset_random_seed_stochastic_duration_false():

    params = {
        "opt_stochastic_duration": False,
        "dt": 10,
        "output_interval": 2.,
        "run_duration": 200.,
        "record_rain": True,
        "m_sp": 0.5,
        "n_sp": 1.0,
        "water_erodability~stochastic": 0.01,
        "regolith_transport_parameter": 0.1,
        "infiltration_capacity": 0.0,
        "daily_rainfall__mean_intensity": 1.,
        "daily_rainfall_intermittency_factor": 0.1,
        "daily_rainfall__precipitation_shape_factor": 0.6,
        "number_of_sub_time_steps": 1,
        "random_seed": 1234,
    }
    model = BasicSt(params=params)

    model.reset_random_seed()
    depth_1 = []
    for _ in range(10):
        depth_1.append(
            model.rain_generator.generate_from_stretched_exponential(
                model.scale_factor, model.shape_factor
            )
        )

    model.reset_random_seed()
    depth_2 = []
    for _ in range(10):
        depth_2.append(
            model.rain_generator.generate_from_stretched_exponential(
                model.scale_factor, model.shape_factor
            )
        )
    np.testing.assert_array_equal(depth_1, depth_2)


def test_finalize_opt_duration_stochastic_true():
    pass


def test_finalize_opt_duration_stochastic_false():
    pass


def test_float_number_of_sub_time_steps():
    params = {
        "opt_stochastic_duration": False,
        "dt": 10,
        "output_interval": 2.,
        "run_duration": 200.,
        "record_rain": True,
        "m_sp": 0.5,
        "n_sp": 1.0,
        "water_erodability~stochastic": 0.01,
        "regolith_transport_parameter": 0.1,
        "infiltration_capacity": 0.0,
        "daily_rainfall__mean_intensity": 1.,
        "daily_rainfall_intermittency_factor": 0.1,
        "daily_rainfall__precipitation_shape_factor": 0.6,
        "number_of_sub_time_steps": 1.5,
        "random_seed": 1234,
    }
    with pytest.raises(ValueError):
        model = BasicSt(params=params)


# double check if these two options work with BOTH stochastic duration options.
def test_write_storm_sequence_to_file():
    # this works with both
    pass


def test_write_exceedance_frequency_file():
    # this with stochastic duration = False.
    pass


def test_not_specifying_record_rain():
    pass


def test_write_files_no_record():
    pass
    # both of these raise value errors.
