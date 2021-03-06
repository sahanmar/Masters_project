from PeonyPackage.PeonyDb import MongoDb
from Peony_box.active_learning_simulation.utils import active_learning_simulation

# from Peony_box.src.transformators.HuffPost_transformator import (
#    HuffPostTransform as transformator,
# )
from Peony_box.src.transformators.HuffPost_transformator import (
    FastTextWordEmbeddings as transformator,
)
from Peony_database.src.datasets.fake_news import COLLECTION_NAME, COLLECTION_ID

# from Peony_database.src.datasets.Tweets_emotions_dataset import (
#     COLLECTION_NAME as TweetsEmotions_collection_name,
#     COLLECTION_ID as TweetsEmotions_collection_id,
# )
# from Peony_box.src.transformators.TweetsEmotion_transformator import (
#     TweetsEmotionsTransformWordEmbeddings as transformator,
# )
from Peony_box.src.acquisition_functions.functions import (
    entropy_sampling,
)
from Peony_visualization.src.peony_visualization import visualize_two_auc_evolutions

from sklearn.utils import shuffle
import numpy as np


def main():

    api = MongoDb()

    records_1 = api.get_record(
        collection_name=COLLECTION_NAME,
        collection_id=COLLECTION_ID,
        label="Fake",
        limit=200,
    )

    records_2 = api.get_record(
        collection_name=COLLECTION_NAME,
        collection_id=COLLECTION_ID,
        label="True",
        limit=200,
    )

    # tweet_positive_records = api.get_record(
    #     collection_name=TweetsEmotions_collection_name,
    #     collection_id=TweetsEmotions_collection_id,
    #     label=0,
    #     limit=500,
    # )
    # tweet_negative_records = api.get_record(
    #     collection_name=TweetsEmotions_collection_name,
    #     collection_id=TweetsEmotions_collection_id,
    #     label=4,
    #     limit=500,
    # )

    # Define model specifications
    model_1 = "bayesian_dropout_nn_fast_text_embeddings"
    model_2 = "bayesian_dropout_nn_fast_text_embeddings"
    algorithm = "nn"
    acquisition_function_1 = "random"
    acquisition_function_2 = "entropy"
    active_learning_loops = 1
    active_learning_step = 10
    max_active_learning_iters = 10
    initial_training_data_size = 10
    validation_data_size = 400
    category_1 = "SPORTS"
    category_2 = "COMEDY"
    transformation_needed = False

    instances = records_1 + records_2
    labels = [sample["record"]["label"] for sample in records_1 + records_2]

    # instances = tweet_positive_records + tweet_negative_records
    # labels = [
    #     sample["record"]["label"]
    #     for sample in tweet_positive_records + tweet_negative_records
    # ]

    instances_from_db, labels_from_db = shuffle(instances, labels, random_state=0)

    # HuffPostTransform = word_embed_transformator()

    HuffPostTransform = (
        transformator()
    )  # I'm using here not HuffPost transformator but I'm too lazy to change all variable names

    HuffPostTransform.fit(instances_from_db, labels_from_db)

    if transformation_needed:
        instances = instances_from_db
        labels = labels_from_db
    else:
        instances = HuffPostTransform.transform_instances(instances_from_db)
        labels = HuffPostTransform.transform_labels(labels_from_db)

    # Get AUC results from an active learning simulation
    auc_active_learning_random_10_runs_nn = active_learning_simulation(
        HuffPostTransform,
        None,
        active_learning_loops,
        max_active_learning_iters,
        active_learning_step,
        algorithm,
        instances,
        labels,
        initial_training_data_size,
        transformation_needed,
    )

    # Pack specifications and resutls to the list for uploading to Peony Database
    list_to_upload = [
        model_1,
        acquisition_function_1,
        active_learning_loops,
        active_learning_step,
        max_active_learning_iters,
        initial_training_data_size,
        validation_data_size,
        category_1,
        category_2,
        auc_active_learning_random_10_runs_nn,
    ]

    # Upload results to Peony Database
    # api.load_model_results(*list_to_upload)

    # Get AUC results from an active learning simulation
    auc_active_learning_entropy_10_runs_nn = active_learning_simulation(
        HuffPostTransform,
        entropy_sampling,  # false_positive_sampling,
        active_learning_loops,
        max_active_learning_iters,
        active_learning_step,
        algorithm,
        instances,
        labels,
        initial_training_data_size,
        transformation_needed,
    )

    # Pack specifications and resutls to the list for uploading to Peony Database
    list_to_upload = [
        model_2,
        acquisition_function_2,
        active_learning_loops,
        active_learning_step,
        max_active_learning_iters,
        initial_training_data_size,
        validation_data_size,
        category_1,
        category_2,
        auc_active_learning_entropy_10_runs_nn,
    ]

    # Upload results to Peony Database
    # api.load_model_results(*list_to_upload)

    visualize_two_auc_evolutions(
        auc_active_learning_random_10_runs_nn, auc_active_learning_entropy_10_runs_nn
    )


if __name__ == "__main__":
    main()
