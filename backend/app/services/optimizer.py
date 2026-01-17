"""
Local Search Optimizer for Route Generation

Provides utilities for refining routes by nudging GPS points
and evaluating improvements iteratively.
"""

import math
from typing import Callable, Awaitable

# Earth radius in km for coordinate calculations
EARTH_RADIUS_KM = 6378.137


def meters_to_degrees_lat(meters: float) -> float:
    """Convert meters to degrees latitude (roughly constant)."""
    return meters / 111320.0


def meters_to_degrees_lng(meters: float, latitude: float) -> float:
    """Convert meters to degrees longitude (varies by latitude)."""
    lat_rad = math.radians(latitude)
    return meters / (111320.0 * math.cos(lat_rad))


def nudge_point(
    point: tuple[float, float],
    direction: str,
    distance_m: float = 50.0
) -> tuple[float, float]:
    """
    Nudge a GPS point in a cardinal direction.
    
    Args:
        point: (lat, lng) tuple
        direction: 'N', 'S', 'E', 'W'
        distance_m: Distance to nudge in meters
    
    Returns:
        New (lat, lng) tuple
    """
    lat, lng = point
    
    d_lat = meters_to_degrees_lat(distance_m)
    d_lng = meters_to_degrees_lng(distance_m, lat)
    
    if direction == 'N':
        return (lat + d_lat, lng)
    elif direction == 'S':
        return (lat - d_lat, lng)
    elif direction == 'E':
        return (lat, lng + d_lng)
    elif direction == 'W':
        return (lat, lng - d_lng)
    else:
        return point


def nudge_point_set(
    points: list[tuple[float, float]],
    index: int,
    direction: str,
    distance_m: float = 50.0
) -> list[tuple[float, float]]:
    """
    Create a copy of points with one point nudged.
    
    Args:
        points: List of (lat, lng) tuples
        index: Which point to nudge
        direction: 'N', 'S', 'E', 'W'
        distance_m: Nudge distance in meters
    
    Returns:
        New list with the nudged point
    """
    new_points = list(points)
    new_points[index] = nudge_point(points[index], direction, distance_m)
    return new_points


async def local_search_refine(
    seed_points: list[tuple[float, float]],
    evaluate_fn: Callable[[list[tuple[float, float]]], Awaitable[tuple[float, dict]]],
    seed_score: float,
    seed_result: dict,
    max_iterations: int = 3,
    nudge_distance_m: float = 50.0,
    improvement_threshold: float = 1.0,
    skip_first_last: bool = True
) -> tuple[list[tuple[float, float]], float, dict]:
    """
    Refine a route using local search / hill climbing.
    
    For each point (except first/last for loop closure), try nudging
    in 4 directions. Keep the best improvement. Repeat until convergence.
    
    Args:
        seed_points: Initial GPS points
        evaluate_fn: Async function that takes points, returns (score, result_dict)
        seed_score: Score of the seed solution
        seed_result: Result dict of the seed solution
        max_iterations: Maximum refinement passes
        nudge_distance_m: How far to nudge points (in meters)
        improvement_threshold: Minimum score improvement to continue
        skip_first_last: Skip first and last points (for loop closure)
    
    Returns:
        (best_points, best_score, best_result)
    """
    DIRECTIONS = ['N', 'S', 'E', 'W']
    
    current_points = list(seed_points)
    current_score = seed_score
    current_result = seed_result
    
    # Determine which points to optimize
    if skip_first_last and len(current_points) > 2:
        optimize_indices = list(range(1, len(current_points) - 1))
    else:
        optimize_indices = list(range(len(current_points)))
    
    for iteration in range(max_iterations):
        improved_this_round = False
        best_improvement = 0.0
        
        print(f"   🔧 Refinement iteration {iteration + 1}/{max_iterations} (score: {current_score:.2f})")
        
        for idx in optimize_indices:
            for direction in DIRECTIONS:
                # Create candidate with nudged point
                candidate_points = nudge_point_set(
                    current_points, idx, direction, nudge_distance_m
                )
                
                try:
                    candidate_score, candidate_result = await evaluate_fn(candidate_points)
                    
                    improvement = candidate_score - current_score
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_candidate_points = candidate_points
                        best_candidate_score = candidate_score
                        best_candidate_result = candidate_result
                        improved_this_round = True
                        
                except Exception:
                    # Skip failed candidates
                    continue
        
        # Accept best improvement if found
        if improved_this_round and best_improvement >= improvement_threshold:
            current_points = best_candidate_points
            current_score = best_candidate_score
            current_result = best_candidate_result
            print(f"      ✨ Improved by {best_improvement:.2f} -> new score: {current_score:.2f}")
        else:
            # No improvement - converged
            print(f"      📍 Converged (no improvement >= {improvement_threshold})")
            break
    
    return current_points, current_score, current_result
