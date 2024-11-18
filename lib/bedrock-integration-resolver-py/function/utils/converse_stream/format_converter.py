from typing import Any, Dict, List, Union


def from_bedrock_converse_to_bedrock_invoke(
    converse_content: Union[Dict[str, Any], List[Dict[str, Any]]]
):
    """
    Convert Converse API content format to Bedrock Invoke body format.

    Args:
        converse_content: Either a single dictionary or a list of two dictionaries.
            Single dictionary can contain:
                - {"text": "some text"} or
                - {"image": image_data}
            List must contain exactly two dictionaries:
                - [{"text": "some text"}, {"image": image_data}]

    Returns:
        Dictionary formatted according to Bedrock Invoke Model specifications with a body containing
        inputText and/or inputImage.

    Raises:
        ValueError: If input format is invalid or missing required fields.
        TypeError: If input is not a dictionary or list of dictionaries.
    """
    if isinstance(converse_content, dict):
        if "text" not in converse_content and "image" not in converse_content:
            raise ValueError("Dictionary must contain either 'text' or 'image' key")
        body = {}
        if "text" in converse_content:
            body["inputText"] = converse_content["text"]
        if "image" in converse_content:
            body["inputImage"] = converse_content["image"]["source"]["bytes"]
    elif isinstance(converse_content, list):
        if len(converse_content) > 2:
            raise ValueError(
                "List must contain one or two dictionaries including (text and image)"
            )

        body = {}
        for item in converse_content:
            if not isinstance(item, dict):
                raise TypeError("Each item in list must be a dictionary")

            if "text" in item:
                body["inputText"] = item["text"]
            elif "image" in item:
                body["inputImage"] = item["image"]["source"]["bytes"]
            else:
                raise ValueError(
                    "Each dictionary must contain either 'text' or 'image' key"
                )
    else:
        raise TypeError("Input must be either a dictionary or a list of dictionaries")

    return body
