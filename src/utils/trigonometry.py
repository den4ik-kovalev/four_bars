import math


def circle_coords(
    center: (float, float),
    r: float,
    n: int  # Количество точек
) -> list[(float, float)]:

    x0, y0 = center
    result = []
    for i in range(n):
        phi = 2 * math.pi / n * i
        x = x0 + r * math.cos(phi)
        y = y0 + r * math.sin(phi)
        result.append((x, y))
    return result
