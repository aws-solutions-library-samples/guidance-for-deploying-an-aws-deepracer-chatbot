"""
Optimal Race Line Calculator for AWS DeepRacer.

This module calculates the optimal race line for a given track in AWS DeepRacer.
It is designed to run as an AWS Lambda function.

code originates from: https://github.com/cdthompson/deepracer-k1999-race-lines/blob/master/Race-Line-Calculation.ipynb
"""

from typing import List

import numpy as np
from aws_lambda_powertools import Logger
from shapely.geometry import Point, Polygon

logger = Logger()


def __menger_curvature(
    pt1: np.ndarray, pt2: np.ndarray, pt3: np.ndarray, atol: float = 1e-3
) -> float:
    """Calculate the Menger curvature of three points."""
    vec21 = pt1 - pt2
    vec23 = pt3 - pt2

    norm21 = np.linalg.norm(vec21)
    norm23 = np.linalg.norm(vec23)

    theta = np.arccos(np.dot(vec21, vec23) / (norm21 * norm23))
    if np.isclose(theta - np.pi, 0.0, atol=atol):
        theta = 0.0

    dist13 = np.linalg.norm(vec21 - vec23)

    return 2 * np.sin(theta) / dist13


def __improve_race_line(
    old_line: np.ndarray,
    inner_border: np.ndarray,
    outer_border: np.ndarray,
    xi_iterations: int = 4,
) -> np.ndarray:
    """Improve the race line using gradient descent."""
    new_line = old_line.copy()
    ls_inner_border = Polygon(inner_border)
    ls_outer_border = Polygon(outer_border)
    npoints = len(new_line)

    for i in range(npoints):
        xi = new_line[i]
        prevprev = new_line[(i - 2) % npoints]
        prev = new_line[(i - 1) % npoints]
        nexxt = new_line[(i + 1) % npoints]
        nexxtnexxt = new_line[(i + 2) % npoints]

        c1 = __menger_curvature(prevprev, prev, xi)
        c2 = __menger_curvature(xi, nexxt, nexxtnexxt)
        target_ci = (c1 + c2) / 2

        xi_bound1 = xi.copy()
        xi_bound2 = (nexxt + prev) / 2
        p_xi = xi.copy()

        for _ in range(xi_iterations):
            p_ci = __menger_curvature(prev, p_xi, nexxt)
            if np.isclose(p_ci, target_ci):
                break
            if p_ci < target_ci:
                xi_bound2 = p_xi.copy()
                new_p_xi = (xi_bound1 + p_xi) / 2
            else:
                xi_bound1 = p_xi.copy()
                new_p_xi = (xi_bound2 + p_xi) / 2

            if Point(new_p_xi).within(ls_inner_border) or not Point(new_p_xi).within(
                ls_outer_border
            ):
                if p_ci < target_ci:
                    xi_bound1 = new_p_xi.copy()
                else:
                    xi_bound2 = new_p_xi.copy()
            else:
                p_xi = new_p_xi

        new_line[i] = p_xi

    return new_line


def __calculate_optimal_race_line(
    waypoints: List[List[float]], line_iterations: int = 1000, xi_iterations: int = 4
) -> List[List[float]]:
    """
    Calculate the optimal race line for a given track.

    :param waypoints: List of waypoints, where each waypoint is a list of
                      [center_x, center_y, inner_x, inner_y, outer_x, outer_y]
    :param line_iterations: Number of iterations to improve the race line
    :param xi_iterations: Number of iterations for each point improvement
    :return: List of [x, y] coordinates representing the optimal race line
    """
    try:
        # Convert input waypoints to numpy array
        waypoints_array = np.array(waypoints)

        center_line = waypoints_array[:, 0:2]
        inner_border = waypoints_array[:, 2:4]
        outer_border = waypoints_array[:, 4:6]

        race_line = center_line[:-1].copy()
        for i in range(line_iterations):
            race_line = __improve_race_line(
                race_line, inner_border, outer_border, xi_iterations
            )
            if i % 100 == 0:
                logger.info(f"Completed iteration {i}")

        loop_race_line = np.vstack((race_line, race_line[0]))

        # Convert the result back to a list for JSON serialization
        return loop_race_line.tolist()
    except Exception as e:
        logger.exception(f"Error in calculate_optimal_race_line: {e}")
        raise


def calculate_optimal_race_line(waypoints: List[List[float]]) -> dict:
    logger.info(
        f"Starting to calculate optimal racing line...", extra={"waypoints": waypoints}
    )
    if not waypoints or waypoints == "unknown":
        return "You don´t have access to the waypoints for this track"
    calculated_race_line = __calculate_optimal_race_line(waypoints)
    response = f"The optimal race line using waypoints for this track is: {calculated_race_line}. Please note that this is an approximation and may not be the exact optimal race line"
    logger.info(
        f"Finished calculating optimal racing line", extra={"response": response}
    )
    return response
