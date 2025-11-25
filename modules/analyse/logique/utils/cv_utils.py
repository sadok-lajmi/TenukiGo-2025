"""
Computer Vision (CV) Utilities.

A collection of helper functions for image processing, line detection,
intersection finding, clustering, and perspective transformation,
primarily for analyzing Go board images.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from sklearn.cluster import DBSCAN, KMeans

logger = logging.getLogger(__name__)


def line_equation(x1: float, y1: float,
                  x2: float, y2: float) -> Tuple[float, float]:
    """
    Calculates the slope and intercept (y = mx + b) for a line.
    For vertical lines, slope is 'Inf' and intercept is the x-coordinate.
    """
    if x1 == x2:
        slope = float('Inf')
        b = x1
    else:
        slope = (y2 - y1) / (x2 - x1)
        b = y1 - slope * x1
    return slope, b


def normalize_line_direction(lines: np.ndarray) -> np.ndarray:
    """
    Sorts the endpoints of each line so that (x1, y1) is always
    the "top-left-most" point (based on sum of coords).
    """
    for i in range(len(lines)):
        x1, y1, x2, y2 = lines[i]
        if (x1 + y1) > (x2 + y2):
            lines[i] = [x2, y2, x1, y1]
    return lines


def are_similar(line1: np.ndarray, line2: np.ndarray,
                threshold: float = 10.0) -> bool:
    """
    Checks if two lines are similar based on a distance threshold
    for all 4 coordinates.
    """
    line1 = np.array(line1)
    line2 = np.array(line2)
    return np.all(np.abs(line1 - line2) <= threshold)


def removeDuplicates(lines: np.ndarray) -> np.ndarray:
    """
    Groups similar lines and averages them to remove duplicates.
    """
    if len(lines) == 0:
        return np.array([])

    lines_list = lines.tolist() if isinstance(lines, np.ndarray) else list(
        lines)

    grouped_lines: Dict[Tuple, List] = {}
    for line in lines_list:
        x1, y1, x2, y2 = line
        found = False
        for key in list(grouped_lines.keys()):
            if are_similar(np.array(key), np.array(line)):
                grouped_lines[key] = grouped_lines[key] + [line]
                found = True
                break
        if not found:
            grouped_lines[(x1, y1, x2, y2)] = [line]

    final_lines = [
        np.mean(grouped_lines[key], axis=0) for key in grouped_lines
    ]
    return np.array(final_lines).astype(int)


def is_vertical(x1: float, y1: float, x2: float, y2: float) -> bool:
    """Checks if a line is (mostly) vertical."""
    return abs(x1 - x2) < 50 and abs(y1 - y2) > 50


def intersect(line1: np.ndarray, line2: np.ndarray) -> np.ndarray:
    """Finds the (x, y) intersection point of two lines."""
    slope1, b1 = line_equation(*line1)
    slope2, b2 = line_equation(*line2)

    if slope1 == float('Inf'):
        x = b1
        y = slope2 * x + b2
    elif slope2 == float('Inf'):
        x = b2
        y = slope1 * x + b1
    elif slope1 == slope2:
        logger.warning("Intersect called on parallel lines. Returning (0,0).")
        return np.array([0, 0])
    else:
        x = (b2 - b1) / (slope1 - slope2)
        y = slope1 * x + b1

    return np.array([int(np.round(x)), int(np.round(y))])


def map_intersections(
    intersections: np.ndarray, board_size: int = 19
) -> Dict[Tuple[int, int], Tuple[int, int]]:
    """
    Creates a dictionary mapping (x, y) pixel coordinates to (col, row)
    board indices (0-18).
    """
    sorted_indices = np.lexsort((intersections[:, 0], intersections[:, 1]))
    cleaned_intersections = intersections[sorted_indices].tolist()

    board_map: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for j in range(board_size):  # Row index
        row_points = cleaned_intersections[:board_size]
        cleaned_intersections = cleaned_intersections[board_size:]

        if not row_points or len(row_points) < board_size:
            logger.warning(
                f"Incomplete grid at row {j}. "
                f"Expected {board_size} points, found {len(row_points)}"
            )
            break

        row_points.sort(key=lambda p: p[0])

        for i in range(board_size):  # Column index
            if row_points:
                board_map[tuple(row_points.pop(0))] = (i, j)

    return board_map


def detect_intersections(cluster_1: np.ndarray,
                         cluster_2: np.ndarray,
                         image: np.ndarray) -> np.ndarray:
    """
    Detects intersection points between two clusters of lines.
    """
    intersections = []

    # This logic is from the original utils_.py
    if hasattr(image, 'shape'):
        if callable(image.shape):
            img_height, img_width = image.shape()[:2]
        else:
            img_height, img_width = image.shape[:2]
    else:
        raise ValueError(f"Image object has no 'shape' attribute. "
                         f"Type: {type(image)}")

    for v_line in cluster_1:
        for h_line in cluster_2:
            inter = intersect(v_line, h_line)
            inter_x = int(inter[0])
            inter_y = int(inter[1])

            if (0 <= inter_x < img_width) and (0 <= inter_y < img_height):
                intersections.append((inter_x, inter_y))

    return np.array(intersections)


def calculate_distances(lines: np.ndarray) -> List[float]:
    """
    Calculate average distances between consecutive lines in a sorted list.
    """
    distances = []
    for i in range(len(lines) - 1):
        dist_start = np.linalg.norm(lines[i + 1][:2] - lines[i][:2])
        dist_end = np.linalg.norm(lines[i + 1][2:] - lines[i][2:])
        distances.append((dist_start + dist_end) / 2)
    return distances


def find_common_distance(
    distances: List[float], target_distance: float = 30.0
) -> Tuple[float, np.ndarray]:
    """
    Finds the most common grid spacing distance using DBSCAN clustering.
    """
    distances_reshaped = np.array(distances).reshape((-1, 1))

    dbscan = DBSCAN(eps=1, min_samples=1)
    labels = dbscan.fit_predict(distances_reshaped)

    means = []
    label_indices = []

    for label in np.unique(labels):
        if label == -1:  # Skip noise points
            continue
        means.append(np.mean(distances_reshaped[labels == label]))
        label_indices.append(label)

    if not means:
        logger.warning("DBSCAN found no clusters, returning mean of all.")
        # Handle case where all points might be noise
        if len(distances) == 0:
            return 0.0, np.array([])
        return np.mean(distances), distances_reshaped

    # Find the cluster mean closest to the target distance
    index = np.argmin(np.abs(np.array(means) - target_distance))
    chosen_label = label_indices[index]

    return means[index], distances_reshaped[labels == chosen_label]


def is_approx_multiple(value: float, base: float, threshold: float) -> bool:
    """
    Checks if a value is approximately a multiple of a base, +/- a threshold.
    """
    if base == 0:
        return False
    if value < base:
        return (base - value) < threshold
    check_under = abs((value % base) - base) < threshold
    check_over = abs(value % base) < threshold
    return check_under or check_over


def restore_and_remove_lines(lines: np.ndarray,
                             distance_threshold: float = 10.0) -> np.ndarray:
    """
    Restores missing grid lines and removes spurious lines.
    """
    if len(lines) == 0:
        return lines

    # Sort lines based on their first coordinate (x or y)
    lines = lines[lines[:, 0].argsort()]
    if not is_vertical(*lines[0]):
        # If not vertical, sort by y-coordinate (y1)
        lines = lines[lines[:, 1].argsort()]

    distances = calculate_distances(lines)

    if len(distances) <= 1:
        return lines

    mean_distance, _ = find_common_distance(distances)
    if mean_distance == 0:
        logger.warning("Mean distance is 0, cannot restore lines.")
        return lines

    restored_lines = []
    i = 0
    while i < len(lines) - 1:
        dist_start = np.linalg.norm(lines[i + 1][:2] - lines[i][:2])
        dist_end = np.linalg.norm(lines[i + 1][2:] - lines[i][2:])
        spacing = (dist_start + dist_end) / 2

        if is_approx_multiple(spacing, mean_distance, distance_threshold):
            if spacing >= mean_distance:
                num_missing_lines = round(spacing / mean_distance) - 1
                for j in range(1, num_missing_lines + 1):
                    if is_vertical(*lines[i]):
                        x1 = lines[i][0] + j * mean_distance
                        y1 = lines[i][1]
                        x2 = lines[i][2] + j * mean_distance
                        y2 = lines[i][3]
                    else:
                        x1 = lines[i][0]
                        y1 = lines[i][1] + j * mean_distance
                        x2 = lines[i][2]
                        y2 = lines[i][3] + j * mean_distance
                    restored_lines.append([x1, y1, x2, y2])
        else:
            # Spacing is not a multiple, remove the next line as spurious
            lines = np.delete(lines, i + 1, axis=0)
            i -= 1  # Re-check distances from the current line
        i += 1

    if restored_lines:
        lines = np.append(lines, np.array(restored_lines, dtype=int), axis=0)

    # Re-sort after additions
    lines = lines[lines[:, 0].argsort()]
    if not is_vertical(*lines[0]):
        lines = lines[lines[:, 1].argsort()]

    return lines


def non_max_suppression(boxes: np.ndarray,
                        overlap_thresh: float = 0.5) -> np.ndarray:
    """
    Applies non-maximum suppression (NMS) to remove redundant bounding boxes.
    """
    if len(boxes) == 0:
        return np.array([])

    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    pick = []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        overlap = (w * h) / area[idxs[:last]]

        delete_indices = np.concatenate(
            ([last], np.where(overlap > overlap_thresh)[0])
        )
        idxs = np.delete(idxs, delete_indices)

    return boxes[pick].astype("int")


def _cluster_lines(all_intersections: np.ndarray,
                   axis: int,
                   n_clusters: int = 19,
                   is_horizontal: bool = False,
                   output_edge: int = 600) -> np.ndarray:
    """
    Helper to cluster intersection points into lines.
    `axis=0` for vertical lines (cluster on x),
    `axis=1` for horizontal (cluster on y).
    """
    if all_intersections.size == 0:
        raise ValueError("No intersection points provided to _cluster_lines.")

    # Reshape for KMeans
    coords = all_intersections[:, axis].reshape((-1, 1))
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=0)
    kmeans.fit(coords)
    cluster_labels = kmeans.labels_
    unique_labels, label_counts = np.unique(cluster_labels, return_counts=True)
    # Process clusters with more points first for better stability
    sorted_unique_labels = unique_labels[np.argsort(label_counts)[::-1]]

    lines_equations = []
    lines_points_length = []
    cluster_lines = []

    for label in sorted_unique_labels:
        mask = (cluster_labels == label)
        line_points = all_intersections[mask]

        if len(line_points) > 2:
            # Fit a line to the points
            if is_horizontal:
                # y = f(x)
                fit_x, fit_y = line_points[:, 0], line_points[:, 1]
            else:
                # x = f(y)
                fit_x, fit_y = line_points[:, 1], line_points[:, 0]

            slope, intercept = np.polyfit(fit_x, fit_y, 1)
            lines_equations.append([slope, intercept])
            lines_points_length.append(len(line_points))
        else:
            # Not enough points, extrapolate
            if not cluster_lines:
                raise Exception("BoardDetection: Cannot reconstruct lines.")

            if len(line_points) < 1:
                raise Exception("BoardDetection: Empty cluster, "
                                "cannot reconstruct line.")

            x1, y1 = line_points[0]
            slope_avg = np.average(np.array(lines_equations)[:, 0],
                                   weights=lines_points_length, axis=0)
            if is_horizontal:
                intercept = y1 - slope_avg * x1
            else:
                intercept = x1 - slope_avg * y1
            lines_equations.append([slope_avg, intercept])
            lines_points_length.append(len(line_points))

        # Create line segment endpoints
        if is_horizontal:
            # y = slope * x + intercept
            line_ = [0, intercept,
                     output_edge, slope * output_edge + intercept]
        else:
            # x = slope * y + intercept
            line_ = [intercept, 0,
                     slope * output_edge + intercept, output_edge]
        cluster_lines.append(line_)

    cluster_lines_np = normalize_line_direction(np.array(cluster_lines))

    # Sort vertical by x1, horizontal by y1
    sort_axis = 1 if is_horizontal else 0
    cluster_lines_np = cluster_lines_np[
        cluster_lines_np[:, sort_axis].argsort()]

    return cluster_lines_np.astype(int)


def detect_lines(
    model_results: Any, perspective_matrix: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Identifies and clusters all line intersections from model results.
    'model_results' is expected to be a YOLO-like results object.

    This function is based on the *working logic* from utils_.py.
    """
    # Class 3: empty_intersection, 4: empty_corner, 5: empty_edge
    empty_intersections = get_key_points(model_results, 3, perspective_matrix)
    empty_corner = get_key_points(model_results, 4, perspective_matrix)
    empty_edge = get_key_points(model_results, 5, perspective_matrix)

    # Ensure all arrays are contiguous
    if empty_intersections.size > 0:
        empty_intersections = np.ascontiguousarray(empty_intersections)
    if empty_corner.size > 0:
        empty_corner = np.ascontiguousarray(empty_corner)
    if empty_edge.size > 0:
        empty_edge = np.ascontiguousarray(empty_edge)

    arrays = [arr for arr in [empty_intersections, empty_corner, empty_edge]
              if arr.size > 0]

    if not arrays:
        raise Exception("No intersection points detected!")

    all_intersections = np.concatenate(arrays, axis=0)

    # --- Detect Vertical Lines (cluster by x-coord) ---
    # This logic is preserved from utils_.py
    cluster_vertical = _cluster_lines(
        all_intersections, axis=0, n_clusters=19, is_horizontal=False
    )

    # --- Detect Horizontal Lines (cluster by y-coord) ---
    # This logic is preserved from utils_.py
    cluster_horizontal = _cluster_lines(
        all_intersections, axis=1, n_clusters=19, is_horizontal=True
    )

    return (
        np.array(cluster_vertical).reshape((-1, 4)),
        np.array(cluster_horizontal).reshape((-1, 4))
    )


def get_corners_inside_box(corners_boxes: np.ndarray,
                           board_box: np.ndarray) -> np.ndarray:
    """
    Filters a list of boxes to find those with at least one corner
    inside a main bounding box.
    """
    board_box = np.array(board_box)
    x1, y1, x2, y2 = board_box

    sq_x1, sq_y1 = corners_boxes[:, 0], corners_boxes[:, 1]
    sq_x2, sq_y2 = corners_boxes[:, 2], corners_boxes[:, 3]

    # Check if any of the 4 corners of a box are inside the board_box
    c1_in = (sq_x1 >= x1) & (sq_x1 <= x2) & (sq_y1 >= y1) & (sq_y1 <= y2)
    c2_in = (sq_x2 >= x1) & (sq_x2 <= x2) & (sq_y1 >= y1) & (sq_y1 <= y2)
    c3_in = (sq_x1 >= x1) & (sq_x1 <= x2) & (sq_y2 >= y1) & (sq_y2 <= y2)
    c4_in = (sq_x2 >= x1) & (sq_x2 <= x2) & (sq_y2 >= y1) & (sq_y2 <= y2)

    condition = c1_in | c2_in | c3_in | c4_in
    return corners_boxes[condition]


def get_corners(results: Any,
                padding: Optional[float] = None) -> np.ndarray:
    """
    Extracts the four corner-centers of the board from YOLO results.

    This function uses the *working logic* from utils_.py.
    """
    # Class 2 == "corner"
    # This line is from the working utils_.py
    # It must be np.array() not .cpu().numpy()
    corner_boxes = np.array(results[0].boxes.xyxy[results[0].boxes.cls == 2])

    if len(corner_boxes) < 4:
        raise Exception(f"Incorrect number of corners! "
                        f"Detected {len(corner_boxes)} corners")

    corner_boxes_nms = non_max_suppression(corner_boxes)

    # Class 1 == "board"
    board_box = results[0].boxes.xyxy[results[0].boxes.cls == 1].cpu().numpy()
    if len(board_box) == 0:
        raise Exception("No 'board' (class 1) detected!")
    model_board_edges = board_box[0]

    corner_boxes = get_corners_inside_box(corner_boxes_nms,
                                          np.array(model_board_edges))

    if len(corner_boxes) != 4:
        raise Exception(f"Incorrect number of corners! Detected "
                        f"{len(corner_boxes)} after NMS/filtering.")

    # Get centers of the corner boxes
    corner_centers = ((corner_boxes[:, [0, 1]] +
                       corner_boxes[:, [2, 3]]) / 2)

    # Sort corners into [top-left, top-right, bottom-right, bottom-left]
    # 1. Sort by y-coordinate
    corner_centers = corner_centers[corner_centers[:, 1].argsort()]
    # 2. Sort top 2 by x-coord
    upper = corner_centers[:2][corner_centers[:2][:, 0].argsort()]
    # 3. Sort bottom 2 by x-coord (descending)
    lower = corner_centers[2:][corner_centers[2:][:, 0].argsort()[::-1]]
    corner_centers = np.concatenate((upper, lower)).astype(np.float32)

    if padding is not None:
        corner_centers[0] += np.array([-padding, -padding])  # tl
        corner_centers[1] += np.array([padding, -padding])   # tr
        corner_centers[2] += np.array([padding, padding])    # br
        corner_centers[3] += np.array([-padding, padding])   # bl

    return corner_centers


def get_key_points(results: Any,
                   class_id: int,
                   perspective_matrix: np.ndarray,
                   output_edge: int = 600) -> np.ndarray:
    """
    Extracts and transforms key points (like stones) from YOLO results.
    'results' is expected to be a YOLO-like results object.

    This function uses the *working logic* from utils_.py.
    """
    # Get the boxes that match the class_id
    mask = results[0].boxes.cls == class_id

    # --- CRITICAL: Handle tensor vs. numpy ---
    # Convert to CPU numpy immediately to avoid tensor issues
    if hasattr(results[0].boxes.xywh, 'cpu'):
        xywh_data = results[0].boxes.xywh.cpu().numpy()
    else:
        xywh_data = np.array(results[0].boxes.xywh)

    if hasattr(mask, 'cpu'):
        mask = mask.cpu().numpy()
    else:
        mask = np.array(mask)
    # --- End Fix ---

    # CRITICAL: Use np.copy() to ensure contiguous memory
    key_points = np.copy(xywh_data[mask])

    # If no points detected, return empty array immediately
    if len(key_points) == 0:
        return np.array([]).reshape((0, 2))

    # Reshape to ensure correct dimensions
    key_points = key_points.reshape((-1, 4))

    # Get center points (x, y) from (x, y, w, h)
    key_points = np.copy(key_points[:, [0, 1]])

    # Apply perspective transform
    key_points_for_transform = np.ascontiguousarray(key_points,
                                                    dtype=np.float32)
    key_points_transf = cv2.perspectiveTransform(
        key_points_for_transform.reshape((1, -1, 2)),
        perspective_matrix
    ).reshape((-1, 2))

    # CRITICAL: Make a contiguous copy before filtering
    key_points_transf = np.ascontiguousarray(key_points_transf)

    # Filter points that are outside the warped (0, 600) image bounds
    mask_ge_0 = (key_points_transf >= 0).all(axis=1)
    mask_le_edge = (key_points_transf <= output_edge).all(axis=1)
    combined_mask = mask_ge_0 & mask_le_edge

    # Return a copy to ensure it's contiguous
    return np.copy(key_points_transf[combined_mask])


def line_distance(line1: np.ndarray, line2: np.ndarray) -> float:
    """
    Calculates the average Euclidean distance between two line segments'
    endpoints.
    """
    line1 = np.array(line1)
    line2 = np.array(line2)
    dist_start = np.linalg.norm(line1[:2] - line2[:2])
    dist_end = np.linalg.norm(line1[2:] - line2[2:])
    return (dist_start + dist_end) / 2


def average_distance(lines: np.ndarray) -> float:
    """
    Calculates the average distance between consecutive lines in a list.
    """
    if len(lines) < 2:
        return 0.0

    distances = [line_distance(lines[i + 1], lines[i])
                 for i in range(len(lines) - 1)]
    return np.average(distances)


def add_lines_in_the_edges(lines: np.ndarray,
                           line_type: str) -> np.ndarray:
    """
    Adds missing 1st or 19th grid lines if they weren't detected.
    Assumes lines are sorted.
    """
    if len(lines) not in [17, 18]:
        # Only try to fix if 1 or 2 lines are missing
        return lines

    mean_distance = average_distance(lines)
    if mean_distance == 0:
        return lines

    appended = False
    output_edge = 600  # Assumed warped image size

    if line_type == "vertical":
        left_border = np.array([0, 0, 0, output_edge])
        right_border = np.array([output_edge, 0, output_edge, output_edge])

        if line_distance(lines[0], left_border) > mean_distance:
            x1 = lines[0][0] - mean_distance
            y1 = lines[0][1]
            x2 = lines[0][2] - mean_distance
            y2 = lines[0][3]
            lines = np.append(lines, [[x1, y1, x2, y2]], axis=0)
            appended = True
        if line_distance(lines[-1], right_border) > mean_distance:
            x1 = lines[-1][0] + mean_distance
            y1 = lines[-1][1]
            x2 = lines[-1][2] + mean_distance
            y2 = lines[-1][3]
            lines = np.append(lines, [[x1, y1, x2, y2]], axis=0)
            appended = True

        if appended:
            lines = lines[lines[:, 0].argsort()]  # Re-sort by x

    elif line_type == "horizontal":
        top_border = np.array([0, 0, output_edge, 0])
        bottom_border = np.array([0, output_edge, output_edge, output_edge])

        if line_distance(lines[0], top_border) > mean_distance:
            x1 = lines[0][0]
            y1 = lines[0][1] - mean_distance
            x2 = lines[0][2]
            y2 = lines[0][3] - mean_distance
            lines = np.append(lines, [[x1, y1, x2, y2]], axis=0)
            appended = True
        if line_distance(lines[-1], bottom_border) > mean_distance:
            x1 = lines[-1][0]
            y1 = lines[-1][1] + mean_distance
            x2 = lines[-1][2]
            y2 = lines[-1][3] + mean_distance
            lines = np.append(lines, [[x1, y1, x2, y2]], axis=0)
            appended = True

        if appended:
            lines = lines[lines[:, 1].argsort()]  # Re-sort by y

    return lines.astype(int)
