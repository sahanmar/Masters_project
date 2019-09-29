import json

from pathlib import Path
from typing import Dict, List
from common import create_hash
from tqdm import tqdm


COLLECTION_NAME = "Comments_dataset"


def transorm_data(record: Dict[str, any]) -> Dict[str, any]:
    transormed_record: dict = {}
    transormed_record["datasetName"] = COLLECTION_NAME
    transormed_record["datasetId"] = 4
    transormed_record["record"] = {}
    transormed_record["record"]["id"] = create_hash(
        [record["content"], str(record["metadata"]["first_done_at"])]
    )
    transormed_record["record"]["text"] = {"body": record["content"]}
    transormed_record["record"]["label"] = record["annotation"]["labels"]
    transormed_record["record"]["metadata"] = {
        "first_done_at": record["metadata"]["first_done_at"],
        "last_updated_by": record["metadata"]["last_updated_by"],
    }
    return transormed_record


def load_data(path: Path) -> List[dict]:
    with open(path, "r") as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines]