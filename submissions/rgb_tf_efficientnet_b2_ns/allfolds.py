import os
import pandas as pd
import torch
from pytorch_toolbelt.utils import logit, fs
from typing import List, Union
import numpy as np

from sklearn.calibration import CalibratedClassifierCV
from torch.nn import functional as F
from alaska2 import OUTPUT_PRED_MODIFICATION_FLAG, alaska_weighted_auc, OUTPUT_PRED_MODIFICATION_TYPE

output_dir = os.path.dirname(__file__)


def temperature_scaling(x, t):
    x = torch.tensor(x)
    x_l = logit(x)
    x_s = torch.sigmoid(x_l * t)
    return float(x_s)


def sigmoid(x):
    return torch.sigmoid(torch.tensor(x)).item()


def classifier_probas(x):
    x = x.replace("[", "").replace("]", "").split(",")
    x = [float(i) for i in x]
    x = torch.tensor(x).softmax(dim=0)
    x = x[1:].sum()
    return float(x)


def classifier_probas_raw(x):
    x = x.replace("[", "").replace("]", "").split(",")
    x = [float(i) for i in x]
    x = torch.tensor(x)
    x = x[1:].sum()
    return float(x)


def stringify_image_id(x):
    return f"{x:0>4}.jpg"


def submit_from_average_binary(preds: List[str]):
    preds_df = [pd.read_csv(x) for x in preds]

    submission = preds_df[0].copy().rename(columns={"image_id": "Id"})[["Id"]]
    submission["Id"] = submission["Id"].apply(stringify_image_id)
    submission["Label"] = sum([df["pred_modification_flag"].apply(sigmoid).values for df in preds_df]) / len(preds_df)
    return submission


def submit_from_average_classifier(preds: List[str]):
    preds_df = [pd.read_csv(x) for x in preds]

    submission = preds_df[0].copy().rename(columns={"image_id": "Id"})[["Id"]]
    submission["Id"] = submission["Id"].apply(stringify_image_id)
    submission["Label"] = sum([df["pred_modification_type"].apply(classifier_probas).values for df in preds_df]) / len(
        preds_df
    )
    return submission


def submit_from_median_classifier(test_predictions: List[str]):
    preds_df = [pd.read_csv(x) for x in test_predictions]

    p = np.stack([df["pred_modification_type"].apply(classifier_probas).values for df in preds_df])
    p = np.median(p, axis=0)

    submission = preds_df[0].copy().rename(columns={"image_id": "Id"})[["Id"]]
    submission["Id"] = submission["Id"].apply(stringify_image_id)
    submission["Label"] = p
    return submission


def submit_from_binary_calibrated(test_predictions: List[str], oof_predictions: List[str]):
    preds_df = [calibrated(pd.read_csv(x), pd.read_csv(y)) for x, y in zip(test_predictions, oof_predictions)]

    submission = preds_df[0].copy().rename(columns={"image_id": "Id"})[["Id"]]
    submission["Id"] = submission["Id"].apply(stringify_image_id)
    submission["Label"] = sum([df["pred_modification_flag"].values for df in preds_df]) / len(preds_df)
    return submission


def submit_from_classifier_calibrated(test_predictions: List[str], oof_predictions: List[str], winsorized=False):
    if winsorized:
        op = winsorize
    else:
        op = noop

    preds_df = [calibrated(pd.read_csv(x), pd.read_csv(y)) for x, y in zip(test_predictions, oof_predictions)]

    submission = preds_df[0].copy().rename(columns={"image_id": "Id"})[["Id"]]
    submission["Id"] = submission["Id"].apply(stringify_image_id)
    submission["Label"] = sum([op(df["pred_modification_type"].values) for df in preds_df]) / len(preds_df)
    return submission


def submit_from_sum_calibrated(test_predictions: List[str], oof_predictions: List[str]):
    preds_df = [calibrated_sum(pd.read_csv(x), pd.read_csv(y)) for x, y in zip(test_predictions, oof_predictions)]

    submission = preds_df[0].copy().rename(columns={"image_id": "Id"})[["Id"]]
    submission["Id"] = submission["Id"].apply(stringify_image_id)
    submission["Label"] = sum([df["pred_modification_type"].values for df in preds_df]) / len(preds_df)
    return submission


def noop(x):
    return x


def winsorize(x):
    import scipy.stats

    x_w = scipy.stats.mstats.winsorize(x, [0.05, 0.05])
    return x_w

def calibrated(test_predictions, oof_predictions, flag_transform=noop, type_transform=classifier_probas):
    """
    Update test predictions w.r.t to calibration trained on OOF predictions
    :param test_predictions:
    :param oof_predictions:
    :return:
    """
    from sklearn.linear_model import LogisticRegression as LR
    from sklearn.isotonic import IsotonicRegression as IR

    oof_predictions = oof_predictions.copy()
    oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].apply(
        type_transform
    )
    oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].apply(
        flag_transform
    )

    test_predictions = test_predictions.copy()
    test_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = test_predictions[OUTPUT_PRED_MODIFICATION_TYPE].apply(
        type_transform
    )
    test_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = test_predictions[OUTPUT_PRED_MODIFICATION_FLAG].apply(
        flag_transform
    )

    y_true = oof_predictions["true_modification_flag"].values

    print("Calibration results")

    if True:
        ir_flag = IR(out_of_bounds="clip")
        ir_flag.fit(oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values, y_true)
        flag_calibrated = ir_flag.transform(oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values)
        score_flag_before = alaska_weighted_auc(y_true, oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values)
        score_flag_after = alaska_weighted_auc(y_true, flag_calibrated)
        print("Flag", score_flag_before, score_flag_after, (score_flag_after - score_flag_before))
        test_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = ir_flag.transform(
            test_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values
        )

    if True:
        ir_type = IR(out_of_bounds="clip")
        ir_type.fit(oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values, y_true)
        type_calibrated = ir_type.transform(oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values)
        score_type_before = alaska_weighted_auc(y_true, oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values)
        score_type_after = alaska_weighted_auc(y_true, type_calibrated)
        print("Type", score_type_before, score_type_after, score_type_after - score_type_before)
        test_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = ir_type.transform(
            test_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values
        )

    return test_predictions


def calibrated_sum(test_predictions, oof_predictions, flag_transform=sigmoid, type_transform=classifier_probas):
    """
    Update test predictions w.r.t to calibration trained on OOF predictions
    :param test_predictions:
    :param oof_predictions:
    :return:
    """
    from sklearn.linear_model import LogisticRegression as LR
    from sklearn.isotonic import IsotonicRegression as IR

    calib_clf = CalibratedClassifierCV(method="isotonic")

    oof_predictions = oof_predictions.copy()
    oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].apply(
        type_transform
    )
    oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].apply(
        flag_transform
    )

    test_predictions = test_predictions.copy()
    test_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = test_predictions[OUTPUT_PRED_MODIFICATION_TYPE].apply(
        type_transform
    )
    test_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = test_predictions[OUTPUT_PRED_MODIFICATION_FLAG].apply(
        flag_transform
    )

    y_true = oof_predictions["true_modification_flag"].values.astype(int)

    print("Calibration results")

    if True:
        x_uncalibrated = (
            oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values
            + oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values
        )

        calib_clf.fit(x_uncalibrated.reshape(-1, 1), y_true)
        x_calibrated = calib_clf.predict_proba(x_uncalibrated.reshape(-1, 1))[:, 1]
        score_flag_before = alaska_weighted_auc(y_true, x_uncalibrated)
        score_flag_after = alaska_weighted_auc(y_true, x_calibrated)
        print("Sum", score_flag_before, score_flag_after, (score_flag_after - score_flag_before))
        x_test = (
            test_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values
            + test_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values
        )
        x_pred = calib_clf.predict_proba(x_test.reshape(-1, 1))[:, 1]
        test_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = test_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = x_pred

    return test_predictions


def calibrated_raw(test_predictions, oof_predictions, flag_transform=noop, type_transform=classifier_probas):
    """
    Update test predictions w.r.t to calibration trained on OOF predictions
    :param test_predictions:
    :param oof_predictions:
    :return:
    """
    from sklearn.linear_model import LogisticRegression as LR
    from sklearn.isotonic import IsotonicRegression as IR

    oof_predictions = oof_predictions.copy()
    oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].apply(
        type_transform
    )
    oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].apply(
        flag_transform
    )

    test_predictions = test_predictions.copy()
    test_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = test_predictions[OUTPUT_PRED_MODIFICATION_TYPE].apply(
        type_transform
    )
    test_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = test_predictions[OUTPUT_PRED_MODIFICATION_FLAG].apply(
        flag_transform
    )

    y_true = oof_predictions["true_modification_flag"].values.astype(int)

    print("Calibration results")

    if True:
        x_uncalibrated = (
            oof_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values
            + oof_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values
        )

        calib_clf = IR(out_of_bounds="clip")
        calib_clf.fit(x_uncalibrated, y_true)
        x_calibrated = calib_clf.transform(x_uncalibrated)
        score_flag_before = alaska_weighted_auc(y_true, x_uncalibrated)
        score_flag_after = alaska_weighted_auc(y_true, x_calibrated)
        print("Sum", score_flag_before, score_flag_after, (score_flag_after - score_flag_before))
        x_test = (
            test_predictions[OUTPUT_PRED_MODIFICATION_FLAG].values
            + test_predictions[OUTPUT_PRED_MODIFICATION_TYPE].values
        )
        x_pred = calib_clf.transform(x_test)
        test_predictions[OUTPUT_PRED_MODIFICATION_FLAG] = test_predictions[OUTPUT_PRED_MODIFICATION_TYPE] = x_pred

    return test_predictions


def as_hv_tta(predictions):
    return [fs.change_extension(x, "_flip_hv_tta.csv") for x in predictions]


def as_d4_tta(predictions):
    return [fs.change_extension(x, "_d4_tta.csv") for x in predictions]



best_auc_c = [
    "models/Jun02_12_26_rgb_tf_efficientnet_b2_ns_fold2_local_rank_0_fp16/checkpoints_auc_classifier/best_test_predictions.csv",
]

best_auc_c_oof = [
    "models/Jun02_12_26_rgb_tf_efficientnet_b2_ns_fold2_local_rank_0_fp16/checkpoints_auc_classifier/best_oof_predictions.csv",
]


from submissions.ela_skresnext50_32x4d import all_folds as ela_skresnext50_32x4d
from submissions.rgb_tf_efficientnet_b6_ns import allfolds as rgb_tf_efficientnet_b6_ns

submit_from_classifier_calibrated(
    best_auc_c, best_auc_c_oof
).to_csv(
    os.path.join(output_dir, "rgb_tf_efficientnet_b2_fold2_best_c_calibrated.csv"),
    index=None,
)

submit_from_classifier_calibrated(
    best_auc_c
    + ela_skresnext50_32x4d.best_auc_c
    + ela_skresnext50_32x4d.best_auc_b
    + ela_skresnext50_32x4d.best_loss
    + rgb_tf_efficientnet_b6_ns.best_auc_c
    + rgb_tf_efficientnet_b6_ns.best_auc_b
    + rgb_tf_efficientnet_b6_ns.best_loss,
    best_auc_c_oof
    + ela_skresnext50_32x4d.best_auc_c_oof
    + ela_skresnext50_32x4d.best_auc_b_oof
    + ela_skresnext50_32x4d.best_loss_oof
    + rgb_tf_efficientnet_b6_ns.best_auc_c_oof
    + rgb_tf_efficientnet_b6_ns.best_auc_b_oof
    + rgb_tf_efficientnet_b6_ns.best_loss_oof,
).to_csv(
    os.path.join(output_dir, "rgb_tf_efficientnet_b2_rgb_tf_efficientnet_b6_fold01_ela_skresnext50_32x4d_fold0123_best_bcl_calibrated.csv"),
    index=None,
)


def average_predictions(predictions, winsorized=False):

    if winsorized:
        op = winsorize
    else:
        op = noop

    df = [pd.read_csv(x).sort_values(by="Id") for x in predictions]
    return pd.DataFrame.from_dict({"Id": df[0].Id.tolist(), "Label": sum([op(x.Label.values) for x in df]) / len(df)})

#
# #
# #
# submit_from_classifier_calibrated(
#     as_hv_tta(best_loss)
#     # + as_hv_tta(best_auc_b)
#     + as_hv_tta(best_auc_c)
#     + ela_skresnext50_32x4d.best_loss
#     # + ela_skresnext50_32x4d.best_auc_b
#     + ela_skresnext50_32x4d.best_auc_c,
#     as_hv_tta(best_loss_oof)
#     # + as_hv_tta(best_auc_b_oof)
#     + as_hv_tta(best_auc_c_oof)
#     + ela_skresnext50_32x4d.best_loss_oof
#     # + ela_skresnext50_32x4d.best_auc_b_oof
#     + ela_skresnext50_32x4d.best_auc_c_oof,
#     winsorized=False
# ).to_csv(
#     os.path.join(
#         output_dir, "rgb_tf_efficientnet_b6_fold01_d4_ela_skresnext50_32x4d_fold0123_best_cl_calibrated_hv_tta.csv"
#     ),
#     index=None,
# )

#
# submit_from_classifier_calibrated(
#     as_d4_tta(best_loss)
#     + as_d4_tta(best_auc_b)
#     + as_d4_tta(best_auc_c)
#     + ela_skresnext50_32x4d.best_loss
#     + ela_skresnext50_32x4d.best_auc_b
#     + ela_skresnext50_32x4d.best_auc_c,
#     as_d4_tta(best_loss_oof)
#     + as_d4_tta(best_auc_b_oof)
#     + as_d4_tta(best_auc_c_oof)
#     + ela_skresnext50_32x4d.best_loss_oof
#     + ela_skresnext50_32x4d.best_auc_b_oof
#     + ela_skresnext50_32x4d.best_auc_c_oof,
# ).to_csv(
#     os.path.join(
#         output_dir, "rgb_tf_efficientnet_b6_fold01_d4_ela_skresnext50_32x4d_fold0123_best_bcl_calibrated_d4_tta.csv"
#     ),
#     index=None,
# )

# submit_from_classifier_calibrated(
#     as_hv_tta(best_loss) + as_hv_tta(best_auc_c) + as_hv_tta(best_auc_b),
#     as_hv_tta(best_loss_oof) + as_hv_tta(best_auc_c_oof) + as_hv_tta(best_auc_b_oof),
# ).to_csv(os.path.join(output_dir, "rgb_tf_efficientnet_b6_fold01_best_bcl_calibrated_hv_tta.csv"), index=None)
#
# submit_from_classifier_calibrated(
#     ela_skresnext50_32x4d.best_auc_c + ela_skresnext50_32x4d.best_auc_b + ela_skresnext50_32x4d.best_loss,
#     ela_skresnext50_32x4d.best_auc_c_oof + ela_skresnext50_32x4d.best_auc_b_oof + ela_skresnext50_32x4d.best_loss_oof,
# ).to_csv(os.path.join(output_dir, "ela_skresnext50_32x4d_fold01234_best_bcl_calibrated.csv"), index=None)
#
# average_predictions(
#     [
#         os.path.join(output_dir, "rgb_tf_efficientnet_b6_fold01_best_bcl_calibrated_hv_tta.csv"),
#         os.path.join(output_dir, "ela_skresnext50_32x4d_fold01234_best_bcl_calibrated.csv"),
#     ]
# ).to_csv(os.path.join(output_dir, "ela_skresnext50_32x4d_rgb_tf_efficientnet_b6.csv"), index=False)