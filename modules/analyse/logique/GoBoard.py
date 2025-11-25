"""
Board detection and state extraction from camera frames.
"""

import math
import copy
import cv2
import numpy as np
from ultralytics import YOLO
from .utils.cv_utils import (
    get_corners, detect_lines, removeDuplicates,
    restore_and_remove_lines, add_lines_in_the_edges,
    get_key_points, detect_intersections, map_intersections
)


class GoBoard:
    """
    Manages board detection and state extraction.

    Uses YOLO model to find the board, applies perspective correction,
    detects grid lines and stones, and maps stones to intersections.
    """

    def __init__(self, model_path):
        """
        Initialize the GoBoard detector.

        Args:
            model_path: File path to the YOLO model
        """
        self.model = YOLO(model_path)
        self.frame = None
        self.transformed_image = None
        self.annotated_frame = None
        self.state = None
        self.padding = 30
        self.perspective_matrix = None
        self.map = None

    def state_to_array(self):
        """
        Convert internal 19x19x2 state to simple 19x19 array.

        Returns:
            np.array: 19x19 array where 0=empty, 1=black, 2=white

        Raises:
            ValueError: If state hasn't been set
        """
        if self.state is None:
            raise ValueError(
                "The board state is not set. Process a frame first."
            )

        board_array = np.zeros((19, 19), dtype=int)
        board_array[self.state[:, :, 0] == 1] = 1
        board_array[self.state[:, :, 1] == 1] = 2
        return board_array

    def get_state(self):
        """Get deep copy of current 19x19x2 board state."""
        return copy.deepcopy(self.state)

    def apply_perspective_transformation(self, double_transform=False):
        """Warp input frame to get flat, top-down view of board."""
        if double_transform:
            input_points = get_corners(self.results, self.padding)
            output_edge = 600 + self.padding * 2
            out_pts = np.array([
                [0, 0], [output_edge, 0],
                [output_edge, output_edge], [0, output_edge]
            ], dtype=np.float32)

            perspective_matrix = cv2.getPerspectiveTransform(
                input_points, out_pts
            )
            first_transformed_image = cv2.warpPerspective(
                self.frame, perspective_matrix, (output_edge, output_edge)
            )
            self.results = self.model(first_transformed_image, verbose=False)
        else:
            first_transformed_image = self.frame

        self.annotated_frame = self.results[0].plot(labels=False, conf=False)

        input_points = get_corners(self.results, 0)
        output_edge = 600
        out_pts = np.array([
            [0, 0], [output_edge, 0],
            [output_edge, output_edge], [0, output_edge]
        ], dtype=np.float32)

        self.perspective_matrix = cv2.getPerspectiveTransform(
            input_points, out_pts
        )
        self.transformed_image = cv2.warpPerspective(
            first_transformed_image, self.perspective_matrix,
            (output_edge, output_edge)
        )

    def assign_stones(self, white_stones_transf, black_stones_transf,
                      transformed_intersections):
        """Assign detected stones to nearest grid intersection."""
        self.map = map_intersections(transformed_intersections)
        self.state = np.zeros((19, 19, 2))

        for stone in white_stones_transf:
            nearest_corner = self.find_nearest_corner(
                transformed_intersections, stone
            )
            row = self.map[nearest_corner][1]
            col = self.map[nearest_corner][0]
            self.state[row, col, 1] = 1

        for stone in black_stones_transf:
            nearest_corner = self.find_nearest_corner(
                transformed_intersections, stone
            )
            row = self.map[nearest_corner][1]
            col = self.map[nearest_corner][0]
            self.state[row, col, 0] = 1

    def find_nearest_corner(self, transformed_intersections, stone):
        """Find closest intersection to given stone."""
        nearest_corner = None
        closest_distance = float('inf')

        for inter in transformed_intersections:
            distance = math.dist(inter, stone)
            if distance < closest_distance:
                nearest_corner = tuple(inter)
                closest_distance = distance

        return nearest_corner

    def process_frame(self, frame):
        """Run full detection pipeline on a single frame."""
        self.frame = frame
        self.results = self.model(self.frame, verbose=False, conf=0.15)
        self.apply_perspective_transformation(double_transform=False)

        vertical_lines, horizontal_lines = detect_lines(
            self.results, self.perspective_matrix
        )

        vertical_lines = removeDuplicates(vertical_lines)
        horizontal_lines = removeDuplicates(horizontal_lines)
        vertical_lines = restore_and_remove_lines(vertical_lines)
        horizontal_lines = restore_and_remove_lines(horizontal_lines)
        vertical_lines = add_lines_in_the_edges(vertical_lines,
                                                "vertical")
        horizontal_lines = add_lines_in_the_edges(horizontal_lines,
                                                  "horizontal")
        vertical_lines = removeDuplicates(vertical_lines)
        horizontal_lines = removeDuplicates(horizontal_lines)

        black_stones = get_key_points(self.results, 0, self.perspective_matrix)
        white_stones = get_key_points(self.results, 6, self.perspective_matrix)

        vertical_lines = np.array(vertical_lines)
        horizontal_lines = np.array(horizontal_lines)

        v_lines_le_600 = (vertical_lines <= 600).all(axis=1)
        v_lines_ge_0 = (vertical_lines >= 0).all(axis=1)
        h_lines_le_600 = (horizontal_lines <= 600).all(axis=1)
        h_lines_ge_0 = (horizontal_lines >= 0).all(axis=1)

        cluster_1 = vertical_lines[v_lines_le_600 & v_lines_ge_0]
        cluster_2 = horizontal_lines[h_lines_le_600 & h_lines_ge_0]

        if len(cluster_1) != 19 or len(cluster_2) != 19:
            raise Exception(
                f"Incorrect number of lines detected: {len(cluster_1)} "
                f"vertical, {len(cluster_2)} horizontal"
            )

        intersections = detect_intersections(
            cluster_1, cluster_2, self.transformed_image
        )

        if len(intersections) == 0:
            raise Exception("No intersections were found!")
        if len(intersections) != 361:
            print(
                f"Warning: Only {len(intersections)}/361 intersections found."
                )

        self.assign_stones(white_stones, black_stones, intersections)
