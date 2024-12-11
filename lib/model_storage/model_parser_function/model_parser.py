from typing import Any, Dict

import deepracer_model
from track_manager import TrackManager


def parse_model(local_model_path: str) -> Dict[str, Any]:
    """
    Parse model data from a local model path.

    Args:
        local_model_path (str): The local path to the model files.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed model data.
    """

    # Extract relevant information from the downloaded model files.
    model = deepracer_model.DeepRacerModel(local_model_path)
    model_data: Dict[str, Any] = {}
    model_data["model_metadata_used_for_training"] = model.get_model_meta_data()
    model_data["reward_function_used_for_training"] = model.get_reward_function()
    model_data["hyper_parameters_used_for_training"] = model.get_hyper_parameters()
    model_data["training_results"] = model.get_training_metrics()
    model_data["evaluation_results"] = model.get_evaluation_metrics()
    model_data["track_meta_data"] = TrackManager.get_track_meta_data()

    #    logger.debug("Parsed model", extra={"model_data": model_data})
    return model_data
