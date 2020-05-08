import pickle
import warnings
from collections import defaultdict

from catalyst.utils import any2device
from pytorch_toolbelt.utils import to_numpy
from pytorch_toolbelt.utils.catalyst import report_checkpoint

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

import argparse
import os

import cv2
import pandas as pd
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from alaska2 import *
from sklearn.linear_model import LogisticRegression as LR
from sklearn.isotonic import IsotonicRegression as IR


@torch.no_grad()
def compute_oof_predictions(model, dataset, batch_size=1) -> pd.DataFrame:
    df = defaultdict(list)
    for batch in tqdm(DataLoader(dataset, batch_size=batch_size, pin_memory=True)):
        batch = any2device(batch, device="cuda")

        image_ids = batch[INPUT_IMAGE_ID_KEY]
        y_preds = to_numpy(predict_from_flag(model, batch))
        y_trues = to_numpy(batch[INPUT_TRUE_MODIFICATION_FLAG])
        df["Id"].extend(image_ids)
        df["y_true"].extend(y_trues)
        df["y_pred"].extend(y_preds)

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
    parser.add_argument("-od", "--output-dir", type=str)
    parser.add_argument("-b", "--batch-size", type=int, default=1)
    parser.add_argument("-w", "--workers", type=int, default=0)
    parser.add_argument("--tta", type=str, default=None)
    parser.add_argument("--activation", type=str, default="after_model")

    args = parser.parse_args()

    checkpoint_fnames = args.checkpoint
    data_dir = args.data_dir
    output_dir = args.output_dir
    batch_size = args.batch_size
    workers = args.workers
    tta = args.tta
    activation = args.activation
    features = ["rgb"]

    if output_dir is None:
        dirnames = list(set([os.path.dirname(ck) for ck in checkpoint_fnames]))
        if len(dirnames) == 1:
            output_dir = dirnames[0]
        else:
            raise ValueError(
                "A submission csv file must be specified explicitly since checkpoints exists in various folders"
            )

    print("Submissions will be saved to ", output_dir)
    os.makedirs(output_dir, exist_ok=True)

    test_ds = get_test_dataset(data_dir, features=features)
    outputs = [OUTPUT_PRED_MODIFICATION_FLAG, OUTPUT_PRED_MODIFICATION_TYPE]

    model, checkpoints, required_features = ensemble_from_checkpoints(
        checkpoint_fnames, strict=False, outputs=outputs, activation=activation, tta=tta
    )

    for c in checkpoints:
        report_checkpoint(c)

    model = model.cuda()

    if torch.cuda.device_count() > 1:
        model = nn.DataParallel(model)

    model = model.eval()

    fold = checkpoints[0]["checkpoint_data"]["cmd_args"]["fold"]
    _, valid_ds, _ = get_datasets(data_dir, fold=fold, features=required_features)
    oof_predictions = compute_oof_predictions(model, valid_ds)
    oof_predictions.to_csv(os.path.join(output_dir, "oof_predictions.csv"), index=False)

    print("Uncalibrated", alaska_weighted_auc(oof_predictions["y_true"].values, oof_predictions["y_pred"].values))

    ir = IR(out_of_bounds="clip")
    ir.fit(oof_predictions["y_pred"].values, oof_predictions["y_true"].values)
    p_calibrated = ir.transform(oof_predictions["y_pred"].values)
    print("IR", alaska_weighted_auc(oof_predictions["y_true"].values, p_calibrated))
    with open(os.path.join(output_dir, "calibration.pkl"), "wb") as f:
        pickle.dump(ir, f)

    loader = DataLoader(
        test_ds, batch_size=batch_size, num_workers=workers, pin_memory=True, shuffle=False, drop_last=False
    )

    proposalcsv_flag = defaultdict(list)

    for batch in tqdm(loader):
        batch = any2device(batch, device="cuda")
        probas_flag = to_numpy(predict_from_flag(model, batch))
        probas_flag_cal = ir.transform(probas_flag)

        for i, image_id in enumerate(batch[INPUT_IMAGE_ID_KEY]):
            proposalcsv_flag["Id"].append(image_id + ".jpg")
            proposalcsv_flag["Label"].append(float(probas_flag_cal[i]))

    proposalcsv = pd.DataFrame.from_dict(proposalcsv_flag)
    proposalcsv.to_csv(os.path.join(output_dir, "submission_flag_calibrated.csv"), index=False)
    print(proposalcsv.head())


if __name__ == "__main__":
    main()
