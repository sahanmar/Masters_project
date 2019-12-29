import numpy as np
import time

from PeonyPackage.PeonyDb import MongoDb
from Peony_visualization.src.peony_visualization import calculate_binary_metrics
from Peony_box.src.peony_box_model import PeonyBoxModel
from Peony_box.src.peony_adjusted_models.random_trees_model import PeonyRandomForest

# from Peony_box.src.transformators.HuffPost_transformator import (
#     HuffPostTransformWordEmbeddings as transformator,
# )
# from Peony_database.src.datasets.HuffPost_news_dataset import (
#     COLLECTION_NAME as HuffPost_collection_name,
#     COLLECTION_ID as HuffPost_collection_id,
# )

from Peony_box.src.transformators.TweetsEmotion_transformator import (
    TweetsEmotionsTransformWordEmbeddings as transformator,
)
from Peony_database.src.datasets.Tweets_emotions_dataset import (
    COLLECTION_NAME as TweetsEmotions_collection_name,
    COLLECTION_ID as TweetsEmotions_collection_id,
)

from Peony_box.src.acquisition_functions.functions import (
    entropy_sampling,
    false_positive_sampling,
)
from scipy.sparse import vstack
from sklearn.utils import shuffle

from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score
from Peony_box.src.utils import k_fold_corss_validation, auc_metrics
from sklearn.metrics import accuracy_score


def main():
    api = MongoDb()
    # sport_records = api.get_record(
    #     collection_name=HuffPost_collection_name,
    #     collection_id=HuffPost_collection_id,
    #     label="SPORTS",
    #     limit=50,
    # )

    # comedy_records = api.get_record(
    #     collection_name=HuffPost_collection_name,
    #     collection_id=HuffPost_collection_id,
    #     label="COMEDY",
    #     limit=50,
    # )
    # instances = sport_records + comedy_records
    # labels = [sample["record"]["label"] for sample in sport_records + comedy_records]

    tweet_positive_records = api.get_record(
        collection_name=TweetsEmotions_collection_name,
        collection_id=TweetsEmotions_collection_id,
        label=0,
        limit=200,
    )
    weet_negative_records = api.get_record(
        collection_name=TweetsEmotions_collection_name,
        collection_id=TweetsEmotions_collection_id,
        label=4,
        limit=200,
    )
    instances = tweet_positive_records + weet_negative_records
    labels = [
        sample["record"]["label"]
        for sample in tweet_positive_records + weet_negative_records
    ]

    instances, labels = shuffle(instances, labels, random_state=0)

    Transformator = transformator()
    Transformator.fit(instances, labels)

    peony_model = PeonyBoxModel(
        Transformator, active_learning_step=5, acquisition_function=entropy_sampling,
    )
    # peony_model.random_forest_model.fit(instances[50:], labels[50:])
    # peony_model.bayesian_denfi_nn.reset()
    # peony_model.random_forest_model.epsilon_greedy_coef = 1
    # indexes = peony_model.random_forest_model.get_learning_samples(instances[:50])

    # add_training = [instances[index] for index in indexes.tolist()]
    # add_labels = [labels[index] for index in indexes.tolist()]

    # peony_model.feed_forward_nn.add_new_learning_samples(add_training, add_labels)
    # peony_model.feed_forward_nn.fit(instances, labels)
    # predicted = peony_model.feed_forward_nn.predict(instances)

    start_time = time.time()
    k_fold = k_fold_corss_validation(
        peony_model.bayesian_denfi_nn, Transformator, instances, labels, 2
    )
    print(f"elapsed time is {time.time() - start_time}")

    print(auc_metrics(k_fold))

    scores = [
        accuracy_score(eval["true"], eval["predicted"], normalize=True)
        for eval in k_fold
    ]

    print(scores)
    print("test")


if __name__ == "__main__":
    main()
