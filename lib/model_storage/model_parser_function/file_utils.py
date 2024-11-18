import os
import re
import tarfile
import uuid
from typing import Any, Dict, Optional, Tuple
from zipfile import ZipFile

import boto3
from aws_lambda_powertools import Logger

logger = Logger()
s3_client = boto3.client("s3")


def delete_model_from_s3(bucket_name: str, key: str) -> None:
    """
    Delete an object from an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        key (str): The key (path) of the object to be deleted.

    Returns:
        None
    """
    try:
        response = s3_client.delete_object(Bucket=bucket_name, Key=key)
        logger.info("Object deleted from S3", extra={"response": response, "key": key})
    except s3_client.exceptions.ClientError as e:
        logger.error(
            "Error deleting object from S3", extra={"error": str(e), "key": key}
        )


def delete_model_from_tmp(path: str) -> None:
    """
    Delete a file or directory from the /tmp directory.

    Args:
        path (str): The path to the file or directory to be deleted.

    Returns:
        None
    """
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        logger.info("Deleted file or directory from /tmp", extra={"path": path})
    except OSError as e:
        logger.error(
            "Error deleting file or directory from /tmp",
            extra={"error": str(e), "path": path},
        )


def extract_model_name_from_path(key: str) -> Tuple[str, str]:
    """
    Extract the model name and extension from a file path.

    Args:
        key (str): The file path within the S3 bucket.

    Returns:
        tuple: A tuple containing the model name (str) and file extension (str).
    """
    file_name = os.path.basename(key)
    model_name, ext = os.path.splitext(file_name)

    if ext == ".gz":
        model_name, ext = os.path.splitext(model_name)
        ext = ext + ".gz"

    return model_name, ext


def download_model_from_s3(bucket_name: str, key: str) -> str:
    """
    Download a model from an S3 bucket and return the local file path.

    Args:
        bucket_name (str): The name of the S3 bucket.
        key (str): The file path within the S3 bucket.

    Returns:
        str: The local file path of the downloaded model.
    """
    file_name = os.path.basename(key)
    download_base_path = os.path.join("/tmp", str(uuid.uuid4()))
    os.makedirs(
        download_base_path, exist_ok=True
    )  # Create the intermediate directory if it doesn't exist. else the s3 download will fail.
    download_path = os.path.join(download_base_path, file_name)

    s3_client.download_file(Bucket=bucket_name, Key=key, Filename=download_path)

    return download_path


def extract_model(local_model_file_path: str, file_extension: str) -> Optional[str]:
    """
    Extract DeepRacer model files from a compressed file (tar.gz or zip) and return the extracted model path.

    Args:
        local_model_file_path (str): The path to the compressed model file.
        file_extension (str): The extension of the compressed file ('.tar.gz' or '.zip').

    Returns:
        Optional[str]: The path to the extracted model directory, or None if the file type is not supported.
    """
    model_dir_path = os.path.dirname(local_model_file_path)
    extracted_model_path = os.path.join(model_dir_path, "extracted_model")

    if file_extension == ".tar.gz":
        with tarfile.open(local_model_file_path, "r:gz") as tar:
            # Filter out members with absolute paths or paths containing '../'
            safe_members = [
                m
                for m in tar.getmembers()
                if not os.path.isabs(m.name) and "../" not in m.name
            ]
            tar.extractall(path=extracted_model_path, members=safe_members)
            return extracted_model_path
    elif file_extension == ".zip":
        with ZipFile(local_model_file_path, "r") as zip_file:
            # Filter out members with absolute paths or paths containing '../'
            safe_members = [
                info
                for info in zip_file.infolist()
                if not os.path.isabs(info.filename) and "../" not in info.filename
            ]
            for member in safe_members:
                zip_file.extract(member, path=extracted_model_path)
            return extracted_model_path
    else:
        logger.error(f"Unsupported file type: {file_extension}")
        return None


def extract_sub_from_s3_key(key: str) -> Optional[str]:
    """
    Extract the user identifier (sub) from an S3 key.

    Args:
        key (str): The S3 key to extract the substring from.

    Returns:
        Optional[str]: The extracted sub, or None if no match is found.
    """
    pattern = r"/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/"
    match = re.search(pattern, key)
    if match:
        return match.group(1)
    return None
