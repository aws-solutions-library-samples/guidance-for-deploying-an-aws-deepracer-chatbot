import io
import json
from typing import Dict, List, Optional, Union

import numpy as np
import requests
from aws_lambda_powertools import Logger
from rapidfuzz import fuzz, process

logger = Logger()


class TrackManager:
    def __init__(
        self, tracks_file_path: str = "./deepracer_tracks/deepracer-tracks-v3.json"
    ):
        self.tracks: Dict = self._load_tracks(tracks_file_path)

    def _load_tracks(self, file_path: str) -> Dict:
        """Load tracks from JSON file and convert to dictionary."""
        try:
            with open(file_path, "r") as file:
                tracks_list = json.load(file)
                logger.info(
                    f"Loaded {len(tracks_list)} tracks", extra={"tracks": tracks_list}
                )
                return {track["TrackName"]: track for track in tracks_list}
        except FileNotFoundError:
            raise FileNotFoundError(f"Tracks file not found: {file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {file_path}")

    @staticmethod
    def _load_numpy_from_github(url: str) -> np.ndarray:
        """Load numpy array from GitHub URL."""
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace(
            "/blob/", "/"
        )
        logger.info(f"Loading waypoints numpy array from {raw_url}")
        try:
            response = requests.get(raw_url)
            response.raise_for_status()

            content = io.BytesIO(response.content)
            return np.load(content, allow_pickle=True)
        except requests.RequestException as e:
            logger.error(f"Failed to download file: {e}")
            raise Exception(f"Failed to download file: {e}")
        except Exception as e:
            logger.error(f"Error loading numpy array: {e}")
            raise Exception(f"Error loading numpy array: {e}")

    @staticmethod
    def _find_track(search_term: str, track_list: List[str]) -> Optional[Dict]:
        """Find most similar track name using fuzzy matching."""
        search_term = search_term.lower()
        track_list_lower = [track.lower() for track in track_list]

        result = process.extractOne(
            search_term, track_list_lower, scorer=fuzz.partial_ratio, score_cutoff=60
        )

        if result:
            match, score, index = result
            return {"track_name": track_list[index], "confidence": score}
        return None

    def get_track_by_name(self, track_name: str) -> Union[Dict, str]:
        """
        Get track information by name using fuzzy matching.

        Args:
            track_name: Name of the track to search for

        Returns:
            Dict containing track information or error message string
        """
        try:
            identified_track = self._find_track(track_name, list(self.tracks.keys()))
            if not identified_track:
                return f"{track_name} track could not be found"

            confidence = identified_track["confidence"]
            if confidence < 80:
                return f"{track_name} track could not be found, did you mean {identified_track['track_name']}?"

            track_info = self.tracks[identified_track["track_name"]].copy()

            # Load waypoints if available
            waypoints = "unknown"
            if "Waypoints" in track_info:
                return track_info
            elif "WaypointsNpy" in track_info:
                try:
                    waypoint_npy = self._load_numpy_from_github(
                        track_info["WaypointsNpy"]
                    )
                    waypoints = waypoint_npy.tolist()
                except Exception as e:
                    logger.error(f"Error loading waypoints: {e}")

                track_info.update(
                    {
                        "Waypoints": waypoints,
                        "WaypointsDescription": (
                            "Type: list of [float, float], Range: [[xw,0,yw,0] … [xw,Max-1, yw,Max-1]], "
                            "An ordered list of track-dependent Max milestones along the track center. "
                            "Each milestone is described by a coordinate of (xw,i, yw,i). "
                            "For a looped track, the first and last waypoints are the same. "
                            "For a straight or other non-looped track, the first and last waypoints are different."
                        ),
                    }
                )
            logger.info(
                f"Returning track info for {track_name}",
                extra={"track": track_info},
            )
            return track_info

        except Exception as e:
            return f"Error processing track {track_name}: {str(e)}"
