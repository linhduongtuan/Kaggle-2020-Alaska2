import torch
from pytorch_toolbelt.modules import *
from torch import nn

from alaska2.dataset import *
import numpy as np
import torch.nn.functional as F

__all__ = ["dct_resnet34", "dct_hrnet18"]

from alaska2.dataset import DCTMTX


class DCT(nn.Module):
    def __init__(self):
        super().__init__()
        dctmtx = torch.from_numpy(DCTMTX).view((8,8))
        self.register_buffer("dctmtx", dctmtx)

    def forward(self, x):
        batch, channels, rows, cols = x.size()

        x_unfold = F.unfold(x, kernel_size=(8,8), padding=0, stride=(8,8))
        x_unfold = x_unfold.permute(0,2, 1).reshape(batch, -1, 8, 8)
        torch.bmm()
        dct_fold = F.fold(dct, output_size=(rows, cols), kernel_size=8,stride=1)
        return dct_fold



class DCTModel(nn.Module):
    def __init__(self, dct_encoder: EncoderModule, num_classes, dropout=0):
        super().__init__()
        self.dct_bn = nn.BatchNorm2d(64)
        self.dct_encoder = dct_encoder
        self.pool = GlobalAvgPool2d(flatten=True)
        self.embedding = nn.Sequential(
            nn.Linear(self.dct_encoder.channels[-1], 128),
            nn.BatchNorm1d(128),
            nn.AlphaDropout(dropout),
            nn.ReLU(True),
            nn.Linear(128, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(True),
        )

        self.type_classifier = nn.Linear(128, num_classes)
        self.flag_classifier = nn.Linear(128, 1)

    def forward(self, **kwargs):
        dct = self.dct_bn(kwargs[INPUT_FEATURES_DCT_KEY].float())

        dct_featues = self.pool(self.dct_encoder(dct)[-1])
        x = self.embedding(dct_featues)

        return {
            OUTPUT_PRED_MODIFICATION_FLAG: self.flag_classifier(x),
            OUTPUT_PRED_MODIFICATION_TYPE: self.type_classifier(x),
        }

    @property
    def required_features(self):
        return [INPUT_FEATURES_DCT_KEY]


class DCTModelAllPool(nn.Module):
    def __init__(self, dct_encoder: EncoderModule, num_classes, dropout=0):
        super().__init__()
        self.dct_bn = nn.BatchNorm2d(64 * 3)
        self.dct_encoder = dct_encoder
        self.pool = GlobalAvgPool2d(flatten=True)
        self.dropout = nn.Dropout(dropout)

        features = sum(dct_encoder.channels)
        self.type_classifier = nn.Linear(features, num_classes)
        self.flag_classifier = nn.Linear(features, 1)

    def forward(self, **kwargs):
        image = self.dct_bn(kwargs[INPUT_FEATURES_DCT_KEY])
        features = self.dct_encoder(image)

        features = [self.pool(f) for f in features]
        features = torch.cat(features, dim=1)

        return {
            # OUTPUT_FEATURE_MAP_4: features[0],
            # OUTPUT_FEATURE_MAP_8: features[1],
            # OUTPUT_FEATURE_MAP_16: features[2],
            # OUTPUT_FEATURE_MAP_32: features[3],
            OUTPUT_PRED_EMBEDDING: features,
            OUTPUT_PRED_MODIFICATION_FLAG: self.flag_classifier(self.dropout(features)),
            OUTPUT_PRED_MODIFICATION_TYPE: self.type_classifier(self.dropout(features)),
        }

    @property
    def required_features(self):
        return [INPUT_FEATURES_DCT_KEY]


def dct_resnet34(num_classes=4, dropout=0, pretrained=True):
    dct_encoder = Resnet34Encoder(pretrained=pretrained).change_input_channels(64 * 3)
    return DCTModel(dct_encoder, num_classes=num_classes, dropout=dropout)


def dct_hrnet18(num_classes=4, dropout=0, pretrained=True):
    rgb_encoder = HRNetV2Encoder18(pretrained=pretrained).change_input_channels(64 * 3)
    return DCTModelAllPool(rgb_encoder, num_classes=num_classes, dropout=dropout)
