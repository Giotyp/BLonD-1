import numpy as np
import cupy as cp
from ..utils import bmath as bm

grid_size, block_size = bm.gpuDev().grid_size, bm.gpuDev().block_size
kernels = bm.gpuDev().mod

cugradient = kernels.get_function("cugradient")


def gpu_rf_volt_comp(voltage, omega_rf, phi_rf, bin_centers):
    assert voltage.dtype == bm.precision.real_t
    assert omega_rf.dtype == bm.precision.real_t
    assert phi_rf.dtype == bm.precision.real_t
    assert bin_centers.dtype == bm.precision.real_t

    rf_voltage = cp.zeros(bin_centers.size, bm.precision.real_t)

    rvc = kernels.get_function("rf_volt_comp")

    rvc(args=(voltage, omega_rf, phi_rf, bin_centers,
              np.int32(voltage.size), np.int32(bin_centers.size), rf_voltage),
        block=block_size, grid=grid_size)
    return rf_voltage


def gpu_kick(dt, dE, voltage, omega_rf, phi_rf, charge, n_rf, acceleration_kick):
    assert dt.dtype == bm.precision.real_t
    assert dE.dtype == bm.precision.real_t
    assert omega_rf.dtype == bm.precision.real_t
    assert phi_rf.dtype == bm.precision.real_t

    kick_kernel = kernels.get_function("simple_kick")

    voltage_kick = cp.empty(voltage.size, bm.precision.real_t)
    voltage_kick = charge * voltage

    kick_kernel(args=(dt,
                      dE,
                      np.int32(n_rf),
                      voltage_kick,
                      omega_rf,
                      phi_rf,
                      np.int32(dt.size),
                      bm.precision.real_t(acceleration_kick)),
                block=block_size, grid=grid_size)  # , time_kernel=True)


def gpu_drift(dt, dE, solver, t_rev, length_ratio, alpha_order, eta_0,
              eta_1, eta_2, alpha_0, alpha_1, alpha_2, beta, energy):

    solver = solver.decode('utf-8')
    if solver == "simple":
        solver = np.int32(0)
    elif solver == "legacy":
        solver = np.int32(1)
    else:
        solver = np.int32(2)

    drift = kernels.get_function("drift")

    drift(args=(dt,
                dE,
                solver,
                bm.precision.real_t(t_rev), bm.precision.real_t(length_ratio),
                bm.precision.real_t(alpha_order), bm.precision.real_t(eta_0),
                bm.precision.real_t(eta_1), bm.precision.real_t(eta_2),
                bm.precision.real_t(alpha_0), bm.precision.real_t(alpha_1),
                bm.precision.real_t(alpha_2),
                bm.precision.real_t(beta), bm.precision.real_t(energy),
                np.int32(dt.size)),
          block=block_size, grid=grid_size)  # , time_kernel=True)


def gpu_linear_interp_kick(dt, dE, voltage,
                           bin_centers, charge,
                           acceleration_kick):
    assert dt.dtype == bm.precision.real_t
    assert dE.dtype == bm.precision.real_t
    assert voltage.dtype == bm.precision.real_t
    assert bin_centers.dtype == bm.precision.real_t

    macros = dt.size
    slices = bin_centers.size

    gm_linear_interp_kick_help = kernels.get_function("lik_only_gm_copy")
    gm_linear_interp_kick_comp = kernels.get_function("lik_only_gm_comp")

    voltage_kick = cp.empty(slices - 1, bm.precision.real_t)
    dev_factor = cp.empty(slices - 1, bm.precision.real_t)
    gm_linear_interp_kick_help(args=(dt,
                                     dE,
                                     voltage,
                                     bin_centers,
                                     bm.precision.real_t(charge),
                                     np.int32(slices),
                                     np.int32(macros),
                                     bm.precision.real_t(acceleration_kick),
                                     voltage_kick,
                                     dev_factor),
                               grid=grid_size, block=block_size)  # ,time_kernel=True)

    gm_linear_interp_kick_comp(args=(dt,
                                     dE,
                                     voltage,
                                     bin_centers,
                                     bm.precision.real_t(charge),
                                     np.int32(slices),
                                     np.int32(macros),
                                     bm.precision.real_t(acceleration_kick),
                                     voltage_kick,
                                     dev_factor),
                               grid=grid_size, block=block_size)  # ,time_kernel=True)


def gpu_linear_interp_kick_drift(dt, dE, total_voltage, bin_centers, charge, acc_kick,
                                 solver, t_rev, length_ratio, alpha_order, eta_0, eta_1,
                                 eta_2, beta, energy):
    assert dt.dtype == bm.precision.real_t
    assert dE.dtype == bm.precision.real_t
    assert total_voltage.dtype == bm.precision.real_t
    assert bin_centers.dtype == bm.precision.real_t
    gm_linear_interp_kick_drift_comp = kernels.get_function(
        "lik_drift_only_gm_comp")
    gm_linear_interp_kick_help = kernels.get_function("lik_only_gm_copy")

    macros = dt.size
    slices = bin_centers.size

    voltage_kick = cp.empty(slices - 1, bm.precision.real_t)
    factor = cp.empty(slices - 1, bm.precision.real_t)

    gm_linear_interp_kick_help(args=(dt,
                                     dE,
                                     total_voltage,
                                     bin_centers,
                                     bm.precision.real_t(charge),
                                     np.int32(slices),
                                     np.int32(macros),
                                     bm.precision.real_t(acc_kick),
                                     voltage_kick,
                                     factor),
                               grid=grid_size, block=block_size)  # ,time_kernel=True)
    gm_linear_interp_kick_drift_comp(args=(dt,
                                           dE,
                                           total_voltage,
                                           bin_centers,
                                           bm.precision.real_t(charge),
                                           np.int32(slices),
                                           np.int32(macros),
                                           bm.precision.real_t(acc_kick),
                                           voltage_kick,
                                           factor,
                                           bm.precision.real_t(t_rev),
                                           bm.precision.real_t(length_ratio),
                                           bm.precision.real_t(eta_0),
                                           bm.precision.real_t(beta),
                                           bm.precision.real_t(energy)),
                                     grid=grid_size, block=block_size)  # ,time_kernel=True)


def gpu_slice(dt, profile, cut_left, cut_right):

    assert dt.dtype == bm.precision.real_t
    hybrid_histogram = kernels.get_function("hybrid_histogram")
    sm_histogram = kernels.get_function("sm_histogram")

    n_slices = profile.size
    profile.fill(0)
    if 4*n_slices < bm.gpuDev().attributes['MaxSharedMemoryPerBlock']:
        sm_histogram(args=(dt, profile, bm.precision.real_t(cut_left),
                           bm.precision.real_t(cut_right), np.uint32(n_slices),
                           np.uint32(dt.size)),
                     grid=grid_size, block=block_size, shared_mem=4*n_slices)  # , time_kernel=True)
    else:
        hybrid_histogram(args=(dt, profile, bm.precision.real_t(cut_left),
                               bm.precision.real_t(
                                   cut_right), np.uint32(n_slices),
                               np.uint32(dt.size), np.int32(
            bm.gpuDev().attributes['MaxSharedMemoryPerBlock']/4)),
            grid=grid_size, block=block_size,
            shared_mem=bm.gpuDev().attributes['MaxSharedMemoryPerBlock'])  # , time_kernel=True)


def gpu_synchrotron_radiation(dE, U0, n_kicks, tau_z):
    assert dE.dtype == bm.precision.real_t
    synch_rad = kernels.get_function("synchrotron_radiation")

    synch_rad(args=(dE, bm.precision.real_t(U0/n_kicks), np.int32(dE.size),
                    bm.precision.real_t(tau_z * n_kicks),
                    np.int32(n_kicks)),
              block=block_size, grid=grid_size)


def gpu_synchrotron_radiation_full(dE, U0, n_kicks, tau_z, sigma_dE, energy):
    assert dE.dtype == bm.precision.real_t
    synch_rad_full = kernels.get_function("synchrotron_radiation_full")

    synch_rad_full(args=(dE, bm.precision.real_t(U0/n_kicks), np.int32(dE.size),
                         bm.precision.real_t(sigma_dE),
                         bm.precision.real_t(tau_z * n_kicks),
                         bm.precision.real_t(energy), np.int32(n_kicks)),
                   block=block_size, grid=grid_size)


# def gpu_beam_phase(bin_centers, profile, alpha, omega_rf, phi_rf, bin_size):
#     assert bin_centers.dtype == bm.precision.real_t
#     assert profile.dtype == bm.precision.real_t
#     # assert omega_rf.dtype == bm.precision.real_t
#     # assert phi_rf.dtype == bm.precision.real_t
#
#     beam_phase_v2 = kernels.get_function("beam_phase_v2")
#     beam_phase_sum = kernels.get_function("beam_phase_sum")
#
#     array1 = cp.empty(bin_centers.size, bm.precision.real_t)
#     array2 = cp.empty(bin_centers.size, bm.precision.real_t)
#
#     dev_scoeff = cp.empty(1, bm.precision.real_t)
#     dev_coeff = cp.empty(1, bm.precision.real_t)
#
#     beam_phase_v2(args=(bin_centers, profile,
#                         bm.precision.real_t(alpha),
#                         bm.precision.real_t(omega_rf),
#                         bm.precision.real_t(phi_rf),
#                         bm.precision.real_t(bin_size),
#                         array1, array2, np.int32(bin_centers.size)),
#                   block=block_size, grid=grid_size)
#
#     beam_phase_sum(args=(array1, array2, dev_scoeff, dev_coeff,
#                          np.int32(bin_centers.size)), block=(512, 1, 1),
#                    grid=(1, 1, 1))  # , time_kernel=True)
#
#     # convert to numpy array, then to float
#     return float(dev_scoeff[0].get())


@cp.fuse(kernel_name='beam_phase_helper')
def __beam_phase_helper(bin_centers, profile, alpha, omega_rf, phi_rf):
    base = cp.exp(alpha * bin_centers) * profile
    a = omega_rf * bin_centers + phi_rf
    return base * cp.sin(a), base * cp.cos(a)


def gpu_beam_phase(bin_centers, profile, alpha, omega_rf, phi_rf, bin_size):
    assert bin_centers.dtype == bm.precision.real_t
    assert profile.dtype == bm.precision.real_t

    array1, array2 = __beam_phase_helper(
        bin_centers, profile, alpha, omega_rf, phi_rf)
    # due to the division, the bin_size is not needed
    scoeff = cp.trapz(array1, dx=1)
    ccoeff = cp.trapz(array2, dx=1)

    return float(scoeff / ccoeff)


@cp.fuse(kernel_name='beam_phase_fast_helper')
def __beam_phase_fast_helper(bin_centers, profile, omega_rf, phi_rf):
    a = omega_rf * bin_centers + phi_rf
    return profile * cp.sin(a), profile * cp.cos(a)


def gpu_beam_phase_fast(bin_centers, profile, omega_rf, phi_rf, bin_size):
    assert bin_centers.dtype == bm.precision.real_t
    assert profile.dtype == bm.precision.real_t

    array1, array2 = __beam_phase_fast_helper(
        bin_centers, profile, omega_rf, phi_rf)
    # due to the division, the bin_size is not needed
    scoeff = cp.trapz(array1, dx=1)
    ccoeff = cp.trapz(array2, dx=1)

    return float(scoeff / ccoeff)


def gpu_convolve(signal, kernel, mode='full', result=None):
    if mode != 'full':
        # ConvolutionError
        raise RuntimeError('[convolve] Only full mode is supported')
    if result is None:
        result = cp.empty(len(signal) + len(kernel) - 1,
                          dtype=bm.precision.real_t)
    # real_size = len(signal) + len(kernel) - 1
    # complex_size = real_size // 2 + 1
    # result1 = np.empty(complex_size, dtype=bm.precision.complex_t)
    # result2 = np.empty(complex_size, dtype=bm.precision.complex_t)
    result = bm.irfft(bm.rfft(signal) * bm.rfft(kernel))
    return result


def gpu_interp(x, xp, yp, left=None, right=None, result=None):
    cuinterp = kernels.get_function("cuinterp")

    if not left:
        left = yp[0]
    if not right:
        right = yp[-1]
    if result is None:
        result = cp.empty(x.size, bm.precision.real_t)

    cuinterp(args=(x, np.int32(x.size),
                   xp, np.int32(xp.size),
                   yp, result,
                   bm.precision.real_t(left), bm.precision.real_t(right)),
             block=block_size, grid=grid_size)
    return result

# # ffts dicts, a cache for the plans of the ffts
# plans_dict = {}
# inverse_plans_dict = {}


# def gpu_rfft(dev_a, n=0, result=None):
#     if n == 0 and result is None:
#         n = dev_a.size
#     elif n != 0 and result is None:
#         pass
#     if caller_id is None:
#         result = cp.empty(n // 2 + 1, bm.precision.complex_t)
#     else:
#         result = cp.empty(n // 2 + 1, bm.precision.complex_t)
#     out_size = n // 2 + 1
#     in_size = dev_a.size

#     if n == in_size:
#         dev_in = cp.empty(n, bm.precision.real_t)
#         dev_in = dev_a.astype(dev_in.dtype)
#     else:
#         dev_in = cp.zeros(n, bm.precision.real_t)
#         if n < in_size:
#             dev_in = dev_a[:n].astype(dev_in.dtype)
#         else:
#              dev_in[:in_size] = dev_a.astype(dev_in.dtype)
#     result = fft.rfft(dev_in)
#     return result


# def gpu_irfft(dev_a, n=0, result=None):
#     if n == 0 and result is None:
#         n = 2 * (dev_a.size - 1)
#     elif n != 0 and result is None:
#         pass

#     if caller_id is None:
#         result = cp.empty(n, dtype=bm.precision.real_t)
#     else:
#         result = cp.empty(n, bm.precision.real_t)

#     out_size = n
#     in_size = dev_a.size

#     if out_size == 0:
#         out_size = 2 * (in_size - 1)
#     n = out_size // 2 + 1

#     if n == in_size:
#         dev_in = dev_a
#     else:
#         dev_in = cp.zeros(n, bm.precision.complex_t)
#         if n < in_size:
#             dev_in = dev_a[:n]
#         else:
#             dev_in[:in_size] = dev_a

#     result = fft.irfft(dev_in)
#     return result


# def gpu_rfftfreq(n, d=1.0, result=None):
#     factor = 1 / (d * n)
#     result = factor * cp.asnumpy(cp.arange(0, n // 2 + 1, dtype=bm.precision.real_t))
#     return result
