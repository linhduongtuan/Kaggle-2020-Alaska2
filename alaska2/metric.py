import torch
from catalyst.dl import Callback, RunnerState, CallbackOrder
from pytorch_toolbelt.utils.catalyst import get_tensorboard_logger
from pytorch_toolbelt.utils.torch_utils import to_numpy
from sklearn import metrics
import numpy as np
import torch.nn.functional as F

__all__ = [
    "CompetitionMetricCallback",
    "alaska_weighted_auc",
    "EmbeddingCompetitionMetricCallback",
    "ClassifierCompetitionMetricCallback",
]


def alaska_weighted_auc(y_true, y_pred):
    tpr_thresholds = [0.0, 0.4, 1.0]
    weights = [2, 1]

    fpr, tpr, thresholds = metrics.roc_curve(y_true, y_pred, pos_label=1)

    # size of subsets
    areas = np.array(tpr_thresholds[1:]) - np.array(tpr_thresholds[:-1])

    # The total area is normalized by the sum of weights such that the final weighted AUC is between 0 and 1.
    normalization = np.dot(areas, weights)

    competition_metric = 0
    for idx, weight in enumerate(weights):
        y_min = tpr_thresholds[idx]
        y_max = tpr_thresholds[idx + 1]
        mask = (y_min < tpr) & (tpr < y_max)

        x_padding = np.linspace(fpr[mask][-1], 1, 100)

        x = np.concatenate([fpr[mask], x_padding])
        y = np.concatenate([tpr[mask], [y_max] * len(x_padding)])
        y = y - y_min  # normalize such that curve starts at y=0
        score = metrics.auc(x, y)
        submetric = score * weight
        best_subscore = (y_max - y_min) * weight
        competition_metric += submetric

    return competition_metric / normalization


class EmbeddingCompetitionMetricCallback(Callback):
    def __init__(self, input_key: str, output_key: str, prefix="auc_embedding"):
        super().__init__(CallbackOrder.Metric)
        self.prefix = prefix
        self.input_key = input_key
        self.output_key = output_key
        self.true_labels = []
        self.pred_labels = []

    def on_loader_start(self, state: RunnerState):
        self.true_labels = []
        self.pred_labels = []

    @torch.no_grad()
    def on_batch_end(self, state: RunnerState):
        self.true_labels.extend(to_numpy(state.input[self.input_key]).flatten())

        embedding = state.output[self.output_key].detach().cpu()
        background = torch.zeros(embedding.size(1))
        background[0] = 1

        predicted = 1 - F.cosine_similarity(embedding, background.unsqueeze(0), dim=1).pow_(2)
        self.pred_labels.extend(to_numpy(predicted).flatten())

    def on_loader_end(self, state: RunnerState):
        true_labels = np.array(self.true_labels)
        pred_labels = np.array(self.pred_labels)
        score = alaska_weighted_auc(true_labels, pred_labels)
        state.metrics.epoch_values[state.loader_name][self.prefix] = float(score)

        logger = get_tensorboard_logger(state)
        logger.add_pr_curve(self.prefix, true_labels, pred_labels)


class CompetitionMetricCallback(Callback):
    def __init__(self, input_key: str, output_key: str, prefix="auc"):
        super().__init__(CallbackOrder.Metric)
        self.prefix = prefix
        self.input_key = input_key
        self.output_key = output_key
        self.true_labels = []
        self.pred_labels = []

    def on_loader_start(self, state: RunnerState):
        self.true_labels = []
        self.pred_labels = []

    @torch.no_grad()
    def on_batch_end(self, state: RunnerState):
        self.true_labels.extend(to_numpy(state.input[self.input_key]).flatten())
        self.pred_labels.extend(to_numpy(state.output[self.output_key].sigmoid()).flatten())

    def on_loader_end(self, state: RunnerState):
        true_labels = np.array(self.true_labels)
        pred_labels = np.array(self.pred_labels)
        score = alaska_weighted_auc(true_labels, pred_labels)
        state.metrics.epoch_values[state.loader_name][self.prefix] = float(score)

        logger = get_tensorboard_logger(state)
        logger.add_pr_curve(self.prefix, true_labels, pred_labels)


class ClassifierCompetitionMetricCallback(Callback):
    def __init__(self, input_key: str, output_key: str, prefix="auc_classifier"):
        super().__init__(CallbackOrder.Metric)
        self.prefix = prefix
        self.input_key = input_key
        self.output_key = output_key
        self.true_labels = []
        self.pred_labels = []

    def on_loader_start(self, state: RunnerState):
        self.true_labels = []
        self.pred_labels = []

    @torch.no_grad()
    def on_batch_end(self, state: RunnerState):
        self.true_labels.extend(to_numpy(state.input[self.input_key]).flatten())
        has_mod_type = state.output[self.output_key].softmax(dim=1)[:, 1:].sum(dim=1)
        self.pred_labels.extend(to_numpy(has_mod_type).flatten())

    def on_loader_end(self, state: RunnerState):
        true_labels = np.array(self.true_labels)
        pred_labels = np.array(self.pred_labels)
        score = alaska_weighted_auc(true_labels, pred_labels)
        state.metrics.epoch_values[state.loader_name][self.prefix] = float(score)

        logger = get_tensorboard_logger(state)
        logger.add_pr_curve(self.prefix, true_labels, pred_labels)
