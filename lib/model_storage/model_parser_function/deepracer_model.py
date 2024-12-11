# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import glob
import json
import os

import yaml
from aws_lambda_powertools import Logger
from track_manager import TrackManager

logger = Logger()
track_manager = TrackManager()


class DeepRacerModel:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model_key = ""

    def __get_track_used_for_training(self, training_metrics_file_name):
        """
        Obtain the track used for training from the eval metrics file.

        Args:
            training_metrics_file_name (string): The name of the training metrics file

        Returns:
            The track used for training. If the track is not found, "unknown" is returned.

        """
        try:
            training_params_files = glob.glob(
                f"{self.model_path}/training_params_*.yaml"
            )
            for training_params_file in training_params_files:
                training_settings = open(training_params_file, "r").read()
                track_id = yaml.safe_load(training_settings)["WORLD_NAME"]
                track = track_manager.get_track_by_id(track_id)

                training_direction = "unknown"
                try:
                    is_trained_clockwise = yaml.safe_load(training_settings)[
                        "TRACK_DIRECTION_CLOCKWISE"
                    ]
                    if is_trained_clockwise:
                        training_direction = "CLOCKWISE"
                    else:
                        training_direction = "COUNTER_CLOCKWISE"
                except Exception:
                    training_direction = "COUNTER_CLOCKWISE"
                logger.info(
                    f"Training track: {track['TrackName']}, direction: {training_direction}"
                )

                return {"name": track["TrackName"], "direction": training_direction}
        except Exception:
            logger.exception("Could not obtain the track used for training")
        return "unknown"

    def __get_track_used_for_evaluation(self, evaluation_metrics_file_name):
        """
        Obtain the track used for evaluation from the eval metrics file.

        Args:
            evaluation_metrics_file_key (string): The S3 key for the evaluation metrics file

        Returns:
            The track used for evaluation. If the track is not found, "unknown" is returned.

        """
        try:
            eval_params_files = glob.glob(f"{self.model_path}/eval_params_*.yaml")
            for eval_params_file in eval_params_files:
                eval_settings = open(eval_params_file, "r").read()

                metrics_s3_object_key = yaml.safe_load(eval_settings)[
                    "METRICS_S3_OBJECT_KEY"
                ]
                if evaluation_metrics_file_name in metrics_s3_object_key:
                    track_id = yaml.safe_load(eval_settings)["WORLD_NAME"]
                    track = track_manager.get_track_by_id(track_id)

                    try:
                        is_evaluated_clockwise = yaml.safe_load(eval_settings)[
                            "TRACK_DIRECTION_CLOCKWISE"
                        ]
                        if is_evaluated_clockwise:
                            eval_direction = "CLOCKWISE"
                        else:
                            eval_direction = "COUNTER-CLOCKWISE"
                    except Exception:
                        eval_direction = "COUNTER-CLOCKWISE"
                    logger.info(
                        f"Eval track: {track['TrackName']}, direction: {eval_direction}"
                    )
                    return {"name": track["TrackName"], "direction": eval_direction}
        except Exception:
            logger.exception("Could not obtain the track used for evaluation")
        return "unknown", track_id

    def get_reward_function(self) -> str:
        """
        Get the reward function from the extracted model file.

        Returns:
            The reward function.
        """
        try:
            reward_function_file_path = "reward_function.py"
            file_path = os.path.join(self.model_path, reward_function_file_path)
            reward_function = open(file_path, "r").read()
            return reward_function
        except Exception:
            logger.exception("Could not obtain the reward function")
            raise
        return "unknown"

    def get_hyper_parameters(self):
        """
        Get the hyperparameters used for training the model.

        Returns:
            The hyperparameters used for training the model.
        """
        try:
            hyperparameters_file_path = "ip/hyperparameters.json"
            file_path = os.path.join(self.model_path, hyperparameters_file_path)
            hyperparameters = json.load(open(file_path, "r"))
            return hyperparameters
        except Exception:
            logger.exception("Could not obtain the hyperparameters")
            raise
        return "unknown"

    def get_model_meta_data(self):
        """
        Get the meta data used for training the model.

        Returns:
            The meta data used for training the model.
        """
        try:
            model_meta_data_json_file_path = "model/model_metadata.json"

            file_path = os.path.join(self.model_path, model_meta_data_json_file_path)
            # load a local file given it path
            model_metadata = json.load(open(file_path, "r"))
            return {
                key: model_metadata[key]
                for key in model_metadata.keys()
                & {"action_space", "action_space_type", "sensor"}
            }
        except Exception:
            logger.exception("Could not obtain the model metadata")
        return "unknown"

    def get_training_metrics(self):
        """
        Get the training metrics used for training the model.

        Returns:
            The training metrics used for training the model.
        """
        try:
            training_metrics_file_path = "metrics/training"
            training_log_file_directory_path = os.path.join(
                self.model_path, training_metrics_file_path
            )
            training_metric_files = os.listdir(training_log_file_directory_path)

            for training_metric_file_name in training_metric_files:
                if training_metric_file_name.endswith(".json"):
                    training_metrics = json.load(
                        open(
                            os.path.join(
                                training_log_file_directory_path,
                                training_metric_file_name,
                            ),
                            "r",
                        )
                    )["metrics"]
                    last_evaluation_result_per_iteration = {}
                    for section in training_metrics:
                        if section["phase"] == "evaluation":
                            last_evaluation_result_per_iteration[section["episode"]] = {
                                key: section[key]
                                for key in section.keys()
                                & {
                                    "elapsed_time_in_milliseconds",
                                    "completion_percentage",
                                    "reward_score",
                                    "episode",
                                    "episode_status",
                                }
                            }
                    track = "unknown"
                    try:
                        track = self.__get_track_used_for_training(
                            training_metric_file_name
                        )
                    except Exception:
                        logger.exception(f"Could not get track for training")
                    return {
                        "metrics": list(last_evaluation_result_per_iteration.values()),
                        "track": track,
                    }
        except Exception:
            logger.exception("Could not obtain training metrics")
            raise
        return {"metrics": "unknown", "track": "unknown"}

    def get_evaluation_metrics(self):
        """
        Get the evaluation metrics used for training the model.

        Returns:
            The evaluation metrics used for training the model.
        """
        evaluation_results = []
        try:
            evaluation_metrics_file_path = "metrics/evaluation"
            evaluation_log_files_directory_path = os.path.join(
                self.model_path, evaluation_metrics_file_path
            )
            evaluation_metric_files = os.listdir(evaluation_log_files_directory_path)

            for evaluation_metrics_file_name in evaluation_metric_files:
                if evaluation_metrics_file_name.endswith(".json"):
                    evaluation_metrics = json.load(
                        open(
                            os.path.join(
                                evaluation_log_files_directory_path,
                                evaluation_metrics_file_name,
                            ),
                            "r",
                        )
                    )["metrics"]
                    stripped_evaluation_metrics = []
                    for evaluation_metric in evaluation_metrics:
                        stripped_evaluation_metrics.append(
                            {
                                key: evaluation_metric[key]
                                for key in evaluation_metric.keys()
                                & {
                                    "completion_percentage",
                                    "elapsed_time_in_milliseconds",
                                    "episode_status",
                                    "crash_count",
                                    "reset_count",
                                    "off_track_count",
                                }
                            }
                        )
                    track = "unknown"
                    try:
                        track = self.__get_track_used_for_evaluation(
                            evaluation_metrics_file_name
                        )
                    except Exception:
                        logger.exception("Could not obtain track used for evaluation")

                    fastest_lap_time = "unknown"

                    evaluation_results.append(
                        {
                            "metrics": stripped_evaluation_metrics,
                            "track": track,
                            "fastest_lap_time_by_others_in_milliseconds": fastest_lap_time,
                        }
                    )
        except Exception:
            logger.exception("Could not obtain evaluation metrics")

        if len(evaluation_results) > 0:
            return evaluation_results
        else:
            return [
                {
                    "metrics": "unknown",
                    "track": "unknown",
                    "fastest_lap_time_by_others_in_milliseconds": "unknown",
                }
            ]
