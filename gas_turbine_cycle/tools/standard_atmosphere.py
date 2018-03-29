import numpy as np


r = 6356767  # earth radius
mc = 28.964420   # standard molar mass


def Hconv(H):
    return r * H / (r + H)


def Tzv(H):
    """Starting kinetic temperature Tzv"""
    return float(np.piecewise(
        H,
        [
            -2000 <= H < 0,
            0 <= H < 11000,
            11000 <= H < 20000,
            20000 <= H < 32000,
            32000 <= H < 47000,
            47000 <= H < 51000,
            51000 <= H < 71000,
            71000 <= H < 85000,
            85000 <= H < 94000
            ],
        [
            301.15,
            288.15,
            216.65,
            216.65,
            228.65,
            270.65,
            270.65,
            214.65,
            186.65
        ]
    ))


def Tmzv(H):
    """Starting molar temperature Tmzv"""
    return float(np.piecewise(
        H,
        [
            -2000 <= H < 0,
            0 <= H < 11000,
            11000 <= H < 20000,
            20000 <= H < 32000,
            32000 <= H < 47000,
            47000 <= H < 51000,
            51000 <= H < 71000,
            71000 <= H < 85000,
            85000 <= H < 94000,
            94000 <= H < 102450,
            102450 <= H < 117777,
            117777 <= H <= 120000,
        ],
        [
            301.15,
            288.15,
            216.65,
            216.65,
            228.65,
            270.65,
            270.65,
            214.65,
            186.65,
            186.65,
            211.99,
            380.60
        ]
    ))


def betta(H):
    """gradient betta"""
    return float(np.piecewise(
        H,
        [
            -2000 <= H < 0,
            0 <= H < 11000,
            11000 <= H < 20000,
            20000 <= H < 32000,
            32000 <= H < 47000,
            47000 <= H < 51000,
            51000 <= H < 71000,
            71000 <= H < 85000,
            85000 <= H < 94000,
        ],
        [
            -0.0065,
            -0.0065,
            0,
            0,
            0,
            0,
            -0.0028,
            -0.0020,
            0
        ]
    ))


def bettaM(H):
    """gradient betta molar"""
    return float(np.piecewise(
        H,
        [
            -2000 <= H < 0,
            0 <= H < 11000,
            11000 <= H < 20000,
            20000 <= H < 32000,
            32000 <= H < 47000,
            47000 <= H < 51000,
            51000 <= H < 71000,
            71000 <= H < 85000,
            85000 <= H < 94000,
            94000 <= H < 102450,
            102450 <= H < 117777
        ],
        [
            -0.0065,
            -0.0065,
            0,
            0.0010,
            0.0028,
            0,
            -0.0028,
            -0.0020,
            0,
            0.0030,
            0.0110
        ]
    ))


def Hzv(H):
    """previous H Hzv"""
    return float(np.piecewise(
        H,
        [
            -2000 <= H < 0,
            0 <= H < 11000,
            11000 <= H < 20000,
            20000 <= H < 32000,
            32000 <= H < 47000,
            47000 <= H < 51000,
            51000 <= H < 71000,
            71000 <= H < 85000,
            85000 <= H < 94000,
            94000 <= H < 102450,
            102450 <= H < 117777,
            117777 < H <= 120000
        ],
        [
            -2000,
            0,
            11000,
            20000,
            32000,
            47000,
            51000,
            71000,
            85000,
            94000,
            102450,
            117777
        ]
    ))


def m(H):
    """molar mass"""
    return float(np.piecewise(
        H,
        [
            -2000 <= H < 0,
            0 <= H < 11000,
            11000 <= H < 20000,
            20000 <= H < 32000,
            32000 <= H < 47000,
            47000 <= H < 51000,
            51000 <= H < 71000,
            71000 <= H < 85000,
            85000 <= H < 94000,
            94000 <= H < 102450,
            102450 <= H < 117777,
            117777 < H <= 120000,
        ],
        [
            28.964420,
            28.964420,
            28.964420,
            28.964420,
            28.964420,
            28.964420,
            28.964420,
            28.964420,
            28.964420,
            28.964420,
            27.846000,
            28.450000
        ]
    ))


def pzv(H):
    """pressure start"""
    return float(np.piecewise(
        H,
        [
            0 <= H < 11000,
            11000 <= H < 20000,
            20000 <= H < 32000,
            32000 <= H < 47000,
            47000 <= H < 51000,
            51000 <= H < 71000,
            71000 <= H < 85000,
        ],
        [
            101325,
            22632,
            5474.87,
            868.014,
            110.906,
            66.9384,
            4.47955
        ]
    ))


def TemperatureM(H):
    """temperature molar"""
    return Tmzv(Hconv(H)) + bettaM(Hconv(H)) * (Hconv(H) - Hzv(Hconv(H)))


def temperature(height):
    """thermodynamic"""
    return TemperatureM(height) * m(Hconv(height)) / mc


R = 287.05287
gc = 9.80665


def pressure(height):
    if bettaM(Hconv(height)) == 0:
        return 10 ** (
                np.log10(pzv(Hconv(height))) - (0.434294 * gc) /
                (R * TemperatureM(height) * m(Hconv(height)) / mc) * (Hconv(height) - Hzv(Hconv(height)))
        )
    else:
        return 10 ** (
            np.log10(pzv(Hconv(height))) - gc / (R * bettaM(Hconv(height))) *
            np.log10(
                (Tmzv(Hconv(height)) + bettaM(Hconv(height)) * (Hconv(height) - Hzv(Hconv(height)))) / Tmzv(Hconv(height))
            )
        )