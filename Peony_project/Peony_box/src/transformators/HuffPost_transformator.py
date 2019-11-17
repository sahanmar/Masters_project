import numpy as np

from PeonyPackage.PeonyDb import MongoDb
from Peony_box.src.transformators.generalized_transformator import Transformator
from typing import List, Dict, Any, Union, Optional, Tuple
from Peony_box.src.transformators.common import (
    create_hash,
    lemmatizer,
    stop_words_filter,
    tokenizer,
)
from tqdm import tqdm
from functools import lru_cache

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

COLEECTION_NAME = "Fasttext_pretrained_embeddings"


class HuffPostTransform(Transformator):
    def __init__(self):
        self.transformer = TfidfTransformer(smooth_idf=False)
        self.vectorizer = CountVectorizer()
        self.fitted: bool = False
        self.dict_length: int = 0
        self.encoding_mapper: Dict[str, int] = {}
        self.reverse_mapper: Dict[int, str] = {}

    def fit(self, instances: List[Dict[str, Any]], labels: List[str]) -> None:
        if self.fitted is False:
            print("transforming data...")
            transformed_data = [
                self._transform_text(sample) for sample in tqdm(instances)
            ]
            counts = self.vectorizer.fit_transform(transformed_data)
            self.transformer.fit_transform(counts)
            print("creating labels encoding hash map...")
            self.encoding_mapper = {
                value: index for index, value in enumerate(set(labels))
            }
            self.reverse_mapper = {
                index: value for index, value in enumerate(set(labels))
            }
            self.fitted = True
            self.dict_length = len(self.vectorizer.get_feature_names())

    def transform_instances(self, data: List[Dict[str, Any]]) -> np.ndarray:
        transformed_data = [self._transform_text(sample) for sample in tqdm(data)]
        counts = self.vectorizer.transform(transformed_data)
        return self.transformer.transform(counts)

    def transform_labels(self, data: List[str]) -> np.ndarray:
        transformed_data = [self.transform_label(sample) for sample in tqdm(data)]
        return np.asarray(transformed_data).ravel()

    def reset(self) -> None:
        self.transformer = TfidfTransformer(smooth_idf=False)
        self.vectorizer = CountVectorizer()
        self.fitted = False
        self.dict_length = 0

    @staticmethod
    def _transform_text(sample: Dict[str, Any]) -> str:

        text = " ".join(
            [sample["record"]["text"]["title"], sample["record"]["text"]["body"]]
        )
        return text

    def transform_label(self, sample: str) -> int:
        return self.encoding_mapper[sample]

    def transform_to_label(self, value: int) -> str:
        return self.reverse_mapper[value]


class HuffPostTransformWordEmbeddings(Transformator):
    def __init__(self):
        self.transformer = {}
        self.fitted: bool = False
        self.dict_length: int = 0
        self.api = MongoDb()
        self.encoding_mapper: Dict[str, int] = {}
        self.reverse_mapper: Dict[int, str] = {}

    def fit(self, instances: List[Dict[str, Any]], labels: List[str]) -> None:
        if self.fitted is False:
            print("transforming data...")
            transformed_data = [
                self._transform_text(sample) for sample in tqdm(instances)
            ]
            tokenized_text = [
                token
                for text in transformed_data
                for token in stop_words_filter(tokenizer(text))
            ]
            distinct_tokens = set(tokenized_text)
            print("creating (words -> embeddings) hash map...")
            for token in tqdm(distinct_tokens):
                embedding = self.get_embedding_from_database(token)
                if embedding is not None:
                    self.transformer[token] = embedding
            print("creating labels encoding hash map...")
            self.encoding_mapper = {
                value: index for index, value in enumerate(set(labels))
            }
            self.reverse_mapper = {
                index: value for index, value in enumerate(set(labels))
            }
            self.fitted = True
            self.dict_length = len(self.transformer.keys())

    @staticmethod
    def _normalize(embedding: Union[np.ndarray, List[float]]) -> np.ndarray:
        epsilon = 0.1
        norm = np.linalg.norm(np.asarray(embedding))
        if norm <= epsilon:
            return np.asarray([0.0 for i in range(300)])
        else:
            return np.asarray(embedding) / norm

    def get_embedding_from_database(self, token: str) -> Optional[np.ndarray]:
        embedding = self.api.get_record(
            collection_name="Fasttext_pretrained_embeddings",
            collection_id=11,
            hash=create_hash([token]),
        )[0]
        if embedding is None:
            return [0.0 for i in range(300)]
        else:
            return self._normalize(embedding["record"]["value"])

    def transform_instances(self, data: List[Dict[str, Any]]) -> np.ndarray:
        transformed_data = [self._transform_text(sample) for sample in tqdm(data)]
        return np.asmatrix(
            [
                self._normalize(
                    np.sum(
                        [
                            self.transformer[token]
                            for token in stop_words_filter(tokenizer(text))
                            if token in self.transformer
                        ],
                        axis=0,
                    )
                ).tolist()
                for text in transformed_data
            ]
        )

    def transform_labels(self, data: List[str]) -> np.ndarray:
        transformed_data = [self.transform_label(sample) for sample in tqdm(data)]
        return np.asarray(transformed_data).ravel()

    def reset(self) -> None:
        self.transformer = {}
        self.fitted = False
        self.dict_length = 0

    @staticmethod
    def _transform_text(sample: Dict[str, Any]) -> str:

        text = " ".join(
            [sample["record"]["text"]["title"], sample["record"]["text"]["body"]]
        )
        return text

    def transform_label(self, sample: str) -> int:
        return self.encoding_mapper[sample]

    def transform_to_label(self, value: int) -> str:
        return self.reverse_mapper[value]
