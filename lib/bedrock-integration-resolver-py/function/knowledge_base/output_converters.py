"""
Module for processing and converting vector store results into Converse API content format.

This module provides functionality to transform vector store results containing text and image data
into the Bedrock converse message content format suitable for the Converse API.
"""

from typing import Any, Dict, List

import simplejson as json
from aws_lambda_powertools import Logger
from utils.utils import safe_decode_base64

logger = Logger()


def to_converse_api_content(
    query_results: List[Dict[str, Any]], content_type: str = "context"
) -> List[Dict[str, Any]]:
    """
    Convert query results to Converse API content format.

    Args:
        query_results: List of dictionaries containing query results returned by the vector store.
            Each result can contain either 'text' or 'image' data.
        content_type: Type of content section. Must be either "context" or "examples". Defaults to "context".

    Returns:
        List of dictionaries formatted according to Converse API specifications.

    Example:
        >>> results = [{"text": "<context>"},{"text": "Hello"}, {"image": b"image_bytes"}, {"text": "</context>"}]
        >>> content = to_converse_api_content(results)
        >>> # With examples section
        >>> content = to_converse_api_content(results, content_type="examples")  # Will use <examples> </examples>
    """
    contents = [{"text": f"<{content_type}>"}]
    for result in query_results:
        try:
            if "text" in result:
                contents.append(process_text_result(result))
            elif "image" in result:
                contents.extend(process_image_result(result))
            else:
                logger.warning(f"Unexpected result format: {result}")
        except Exception as e:
            logger.exception(f"Error processing result: {e}")

    contents.append({"text": f"</{content_type}>"})
    return contents


def process_text_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a text result and its metadata.

    Args:
        result: Dictionary containing text content and optional metadata.

    Returns:
        Dictionary with processed text content including metadata if present.
    """
    metadata = parse_metadata(result.get("metadata", "{}"))
    metadata_str = f", <doc_metadata>{metadata}</doc_metadata>" if metadata else ""
    return {"text": f"{result['text']}{metadata_str}"}


def process_image_result(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process an image result and its metadata.

    Args:
        result: Dictionary containing image data and optional metadata.

    Returns:
        List of dictionaries containing processed image data and metadata if present.
    """
    image_data = {
        "format": result.get("format", "png"),
        "source": {"bytes": safe_decode_base64(result["image"])},
    }
    metadata = parse_metadata(result.get("metadata", "{}"))

    contents = [{"image": image_data}]
    if metadata:
        contents.append(
            {"text": f"<image_metadata>{json.dumps(metadata)}</image_metadata>"}
        )
    return contents


def parse_metadata(metadata: Any) -> Dict[str, Any]:
    """
    Parse metadata string or dictionary into a dictionary format.

    Args:
        metadata: Metadata in string or dictionary format.

    Returns:
        Dictionary containing parsed metadata or empty dictionary if parsing fails.
    """
    if isinstance(metadata, dict):
        return metadata
    try:
        return json.loads(metadata)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse metadata: {metadata}")
        return {}
