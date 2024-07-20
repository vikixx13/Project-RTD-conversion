# modules/data_processing.py

import os
import pandas as pd
import numpy as np
import numpy.polynomial.polynomial as poly

ALLOWED_EXTENSIONS = {'txt', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def newton_raphson_method(R_t, R_0=100):
    def newton_raphson(f, f_prime, x0, tol=1e-6, max_iter=100):
        x = x0
        for _ in range(max_iter):
            fx = f(x)
            fpx = f_prime(x)
            if abs(fx) < tol:
                return x
            x -= fx / fpx
        return None  # Did not converge

    A = 3.9083e-3
    B = -5.775e-7
    C = -4.183e-12
    alp = 0.00385

    if abs(R_t - R_0) < 1e-6 or R_t == R_0:
        return 0.0

    if R_t > R_0:
        f = lambda t: R_0 * (1 + A * t + B * t**2) - R_t
        f_prime = lambda t: R_0 * (A + 2 * B * t)
        initial_guess = (R_t - R_0) / (R_0 * alp)
        return newton_raphson(f, f_prime, initial_guess)

    elif 9 < R_t <= R_0:
        f = lambda t: R_0 * (1 + A * t + B * t**2 - 100 * C * t**3 + C * t**4) - R_t
        f_prime = lambda t: R_0 * (A + 2 * B * t - 300 * C * t**2 + 4 * C * t**3)
        initial_guess = (R_t - R_0) / (R_0 * alp)
        return newton_raphson(f, f_prime, initial_guess)

    return None

def polynomial_fit_method(R_t, resistances, temperatures, degree=5):
    coeffs = poly.Polynomial.fit(resistances, temperatures, degree)
    return coeffs(R_t)

def read_resistances(file_path, delimiter):
    try:
        df = pd.read_csv(file_path, delimiter=delimiter, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, delimiter=delimiter, encoding='latin1')
    resistances = df.iloc[:, 0].values
    measured_temperatures = df.iloc[:, 1].values
    return resistances, measured_temperatures

def write_temperatures(resistances, measured_temperatures, calculated_temperatures, errors, output_file):
    df = pd.DataFrame({
        "Resistance (Ohms)": resistances,
        "Measured Temperature (°C)": measured_temperatures,
        "Calculated Temperature (°C)": calculated_temperatures,
        "Error (°C)": errors
    })
    df.to_csv(output_file, index=False)

def calculate_errors(measured_temperatures, calculated_temperatures):
    return [abs(m - c) for m, c in zip(measured_temperatures, calculated_temperatures)]
