import warnings
from collections import defaultdict

from catalyst.utils import any2device
from pytorch_toolbelt.utils import to_numpy, fs
from pytorch_toolbelt.utils.catalyst import report_checkpoint

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

import argparse
import os

import pandas as pd
import numpy as np
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from alaska2 import *


@torch.no_grad()
def compute_test_predictions(model, dataset, batch_size=1, workers=0) -> pd.DataFrame:

    df = defaultdict(list)
    for batch in tqdm(DataLoader(dataset, batch_size=batch_size, num_workers=workers, pin_memory=True)):
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
    parser.add_argument("-dd", "--data-dir", type=str, default=os.environ.get("KAGGLE_2020_ALASKA2"))
    parser.add_argument("-b", "--batch-size", type=int, default=1)
    parser.add_argument("-w", "--workers", type=int, default=0)

    args = parser.parse_args()

    checkpoint_fnames = args.checkpoint
    data_dir = args.data_dir
    batch_size = args.batch_size
    workers = args.workers

    outputs = [OUTPUT_PRED_MODIFICATION_FLAG, OUTPUT_PRED_MODIFICATION_TYPE]

    for checkpoint_fname in checkpoint_fnames:

        model, checkpoints, required_features = ensemble_from_checkpoints(
            [checkpoint_fname], strict=True, outputs=outputs, activation=None, tta=None, temperature=1
        )

        report_checkpoint(checkpoints[0])

        model = model.cuda()
        if torch.cuda.device_count() > 1:
            model = nn.DataParallel(model)
        model = model.eval()

        test_ds = get_test_dataset(data_dir, features=required_features)

        oof_predictions = compute_test_predictions(model, test_ds, batch_size=batch_size, workers=workers)
        oof_predictions_csv = fs.change_extension(checkpoint_fname, "_test_predictions.csv")
        oof_predictions.to_csv(oof_predictions_csv, index=False)

        tta_model = wrap_model_with_tta(model, "flip-hv", inputs=required_features, outputs=outputs).eval()

        oof_predictions = compute_test_predictions(tta_model, test_ds, batch_size=batch_size, workers=workers)
        oof_predictions_csv = fs.change_extension(checkpoint_fname, "_test_predictions_flip_hv_tta.csv")
        oof_predictions.to_csv(oof_predictions_csv, index=False)


if __name__ == "__main__":
    main()