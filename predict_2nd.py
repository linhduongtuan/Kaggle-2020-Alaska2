import warnings

from train_2nd import StackerDataset

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

import argparse
import os
import pandas as pd
import numpy as np
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from collections import defaultdict
from catalyst.utils import any2device
from pytorch_toolbelt.utils import to_numpy, fs
from pytorch_toolbelt.utils.catalyst import report_checkpoint

from alaska2 import *
from alaska2.submissions import sigmoid, parse_classifier_probas, submit_from_average_binary, classifier_probas, \
    just_probas


@torch.no_grad()
def compute_predictions(model, dataset, batch_size=1, workers=0) -> pd.DataFrame:
    df = defaultdict(list)
    for batch in tqdm(
        DataLoader(
            dataset, batch_size=batch_size, num_workers=workers, shuffle=False, drop_last=False, pin_memory=True
        )
    ):
        batch = any2device(batch, device="cuda")

        image_ids = batch[INPUT_IMAGE_ID_KEY]
        df[INPUT_IMAGE_ID_KEY].extend(image_ids)

        outputs = model(**batch)

        if OUTPUT_PRED_MODIFICATION_FLAG in outputs:
            df[OUTPUT_PRED_MODIFICATION_FLAG].extend(to_numpy(outputs[OUTPUT_PRED_MODIFICATION_FLAG]).flatten())

        if OUTPUT_PRED_MODIFICATION_TYPE in outputs:
            df[OUTPUT_PRED_MODIFICATION_TYPE].extend(to_numpy(outputs[OUTPUT_PRED_MODIFICATION_TYPE]).tolist())

    df = pd.DataFrame.from_dict(df)
    return df


@torch.no_grad()
def main():
    # Give no chance to randomness
    torch.manual_seed(0)
    np.random.seed(0)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=str, nargs="+")
    parser.add_argument("-b", "--batch-size", type=int, default=1)
    parser.add_argument("-w", "--workers", type=int, default=0)

    args = parser.parse_args()

    checkpoint_fnames = args.checkpoint
    batch_size = args.batch_size
    workers = args.workers

    outputs = [OUTPUT_PRED_MODIFICATION_FLAG, OUTPUT_PRED_MODIFICATION_TYPE]

    x_test = np.load(f"embeddings_x_test_Gf0_Gf3_Hnrmishf2_Hnrmishf1.npy")
    test_ds = StackerDataset(x_test, None)

    model, checkpoints, required_features = ensemble_from_checkpoints(
        checkpoint_fnames,
        model_name="stacker",
        strict=True, outputs=outputs, activation="after_model", tta=None
    )

    model = model.cuda()
    if torch.cuda.device_count() > 1:
        model = nn.DataParallel(model)
    model = model.eval()

    # Also compute test predictions
    test_predictions_csv = f"2nd_level_stacking_test_raw_predictions_d4.csv"

    test_predictions = compute_predictions(model, test_ds, batch_size=batch_size, workers=workers)
    test_predictions.to_csv(test_predictions_csv, index=False)

    submission = test_predictions.copy().rename(columns={"image_id": "Id"})[["Id"]]
    submission["Id"] = submission["Id"].apply(lambda x: f"{x:04}.jpg")
    # submission["Label"] = test_predictions["pred_modification_type"].apply(just_probas).values
    submission["Label"] = (
        test_predictions["pred_modification_flag"].values
        * test_predictions["pred_modification_type"].apply(just_probas).values
    )

    submission.to_csv("2nd_level_stacking_embeddings_test_submission.csv", index=False)


if __name__ == "__main__":
    main()