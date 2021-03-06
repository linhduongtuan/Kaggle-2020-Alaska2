import itertools
from typing import Tuple, Dict, Optional

import torch
from pytorch_toolbelt.inference.ensembling import Ensembler, ApplySigmoidTo, ApplySoftmaxTo
from torch import nn


from . import rgb_dct, rgb, dct, ela, rgb_ela_blur, timm, ycrcb, hpf_net, srnet, res, bit, timm_bits, unet, stacker
from ..dataset import *
from ..predict import *


MODEL_REGISTRY = {
    "stacker": stacker.StackingModel,
    # Unet
    "nr_rgb_unet": unet.nr_rgb_unet,
    # Big Transfer
    "bit_m_rx152_2": bit.bit_m_rx152_2,
    "bit_m_rx50_1": bit.bit_m_rx50_1,
    "bit_m_rx50_3": bit.bit_m_rx50_3,
    "bit_m_rx101_1": bit.bit_m_rx101_1,
    # TIMM
    "rgb_tresnet_m_448": timm.rgb_tresnet_m_448,
    "rgb_skresnext50_32x4d": timm.rgb_skresnext50_32x4d,
    "rgb_swsl_resnext101_32x8d": timm.rgb_swsl_resnext101_32x8d,
    # EfficientNets (Rounded Input)
    "rgb_tf_efficientnet_b1_ns": timm.rgb_tf_efficientnet_b1_ns,
    "rgb_tf_efficientnet_b2_ns": timm.rgb_tf_efficientnet_b2_ns,
    "rgb_tf_efficientnet_b3_ns": timm.rgb_tf_efficientnet_b3_ns,
    "rgb_tf_efficientnet_b6_ns": timm.rgb_tf_efficientnet_b6_ns,
    "rgb_tf_efficientnet_b7_ns": timm.rgb_tf_efficientnet_b7_ns,
    # EfficientNets (Non-Rounded Input)
    "nr_rgb_tf_efficientnet_b3_ns_mish": timm.nr_rgb_tf_efficientnet_b3_ns_mish,
    "nr_rgb_tf_efficientnet_b3_ns_gn_mish": timm.nr_rgb_tf_efficientnet_b3_ns_gn_mish,
    "nr_rgb_tf_efficientnet_b3_ns_in_mish": timm.nr_rgb_tf_efficientnet_b3_ns_in_mish,
    "nr_rgb_tf_efficientnet_b6_ns": timm.nr_rgb_tf_efficientnet_b6_ns,
    "nr_rgb_tf_efficientnet_b6_ns_mish": timm.nr_rgb_tf_efficientnet_b6_ns_mish,
    "nr_rgb_tf_efficientnet_b6_ns_mish_gep": timm.nr_rgb_tf_efficientnet_b6_ns_mish_gep,
    "nr_rgb_tf_efficientnet_b7_ns_mish": timm.nr_rgb_tf_efficientnet_b7_ns_mish,
    "nr_rgb_mixnet_xl": timm.nr_rgb_mixnet_xl,
    "nr_rgb_mixnet_xxl": timm.nr_rgb_mixnet_xxl,
    # Bits
    "nr_rgb_tf_efficientnet_b3_ns_in_mish_bits": timm_bits.nr_rgb_tf_efficientnet_b3_ns_in_mish_bits,
    "nr_rgb_tf_efficientnet_b3_ns_mish_bits": timm_bits.nr_rgb_tf_efficientnet_b3_ns_mish_bits,
    # RGB + QF
    # "rgb_qf_tf_efficientnet_b2_ns": timm.rgb_qf_tf_efficientnet_b2_ns,
    # "rgb_qf_tf_efficientnet_b6_ns": timm.rgb_qf_tf_efficientnet_b6_ns,
    # "rgb_qf_swsl_resnext101_32x8d": timm.rgb_qf_swsl_resnext101_32x8d,
    # "nr_rgb_tf_efficientnet_b3_ns_mish_mask": timm.nr_rgb_tf_efficientnet_b3_ns_mish_mask,
    "rgb_dct_resnet34": rgb_dct.rgb_dct_resnet34,
    "rgb_dct_efficientb3": rgb_dct.rgb_dct_efficientb3,
    "rgb_dct_seresnext50": rgb_dct.rgb_dct_seresnext50,
    #
    "rgb_b0": rgb.rgb_b0,
    "rgb_resnet18": rgb.rgb_resnet18,
    "rgb_resnet34": rgb.rgb_resnet34,
    "rgb_seresnext50": rgb.rgb_seresnext50,
    "rgb_densenet121": rgb.rgb_densenet121,
    "rgb_densenet201": rgb.rgb_densenet201,
    "rgb_hrnet18": rgb.rgb_hrnet18,
    #
    # DCT
    "dct_seresnext50": dct.dct_seresnext50,
    "dct_efficientnet_b6": dct.dct_efficientnet_b6,
    #
    # ELA
    "ela_tf_efficientnet_b2_ns": ela.ela_tf_efficientnet_b2_ns,
    "ela_tf_efficientnet_b6_ns": ela.ela_tf_efficientnet_b6_ns,
    "ela_skresnext50_32x4d": ela.ela_skresnext50_32x4d,
    "ela_rich_skresnext50_32x4d": ela.ela_rich_skresnext50_32x4d,
    "ela_wider_resnet38": ela.ela_wider_resnet38,
    "ela_ecaresnext26tn_32x4d": ela.ela_ecaresnext26tn_32x4d,
    #
    # Residual
    "res_tf_efficientnet_b2_ns": res.res_tf_efficientnet_b2_ns,
    "rgb_res_tf_efficientnet_b2_ns": res.rgb_res_tf_efficientnet_b2_ns,
    "rgb_res_sms_tf_efficientnet_b2_ns": res.rgb_res_sms_tf_efficientnet_b2_ns,
    "rgb_res_sms_v2_tf_efficientnet_b2_ns": res.rgb_res_sms_v2_tf_efficientnet_b2_ns,
    #
    # YCrCb
    "ycrcb_skresnext50_32x4d": ycrcb.ycrcb_skresnext50_32x4d,
    "ela_s2d_skresnext50_32x4d": ycrcb.ela_s2d_skresnext50_32x4d,
    #
    # HPF
    "hpf_net": hpf_net.hpf_net,
    "hpf_net2": hpf_net.hpf_net_v2,
    "hpf_b3_fixed_gap": hpf_net.hpf_b3_fixed_gap,
    "hpf_b3_covpool": hpf_net.hpf_b3_covpool,
    "hpf_b3_fixed_covpool": hpf_net.hpf_b3_fixed_covpool,
    # SRNET
    "srnet": srnet.srnet,
    "srnet_inplace": srnet.srnet_inplace,
    # OLD STUFF
    "frank": rgb_ela_blur.frank,
}

__all__ = ["MODEL_REGISTRY", "get_model", "ensemble_from_checkpoints", "wrap_model_with_tta"]


def get_model(model_name, num_classes=4, pretrained=True, **kwargs):
    return MODEL_REGISTRY[model_name](num_classes=num_classes, pretrained=pretrained, **kwargs)


def model_from_checkpoint(
    model_checkpoint: str, model_name=None, report=True, need_embedding=False, strict=True
) -> Tuple[nn.Module, Dict]:
    checkpoint = torch.load(model_checkpoint, map_location="cpu")
    model_name = model_name or checkpoint["checkpoint_data"]["cmd_args"]["model"]

    model = get_model(model_name, pretrained=False, need_embedding=need_embedding)
    model.load_state_dict(checkpoint["model_state_dict"], strict=strict)
    return model.eval(), checkpoint


def wrap_model_with_tta(model, tta_mode, inputs, outputs):
    if tta_mode == "flip-hv":
        model = HVFlipTTA(model, inputs=inputs, outputs=outputs, average=True)
    elif tta_mode == "d4":
        model = D4TTA(model, inputs=inputs, outputs=outputs, average=True)
    else:
        pass

    return model


def ensemble_from_checkpoints(
    checkpoints,
    strict=True,
    outputs=None,
    activation: Optional[str] = "after_model",
    tta=None,
    temperature=1,
    need_embedding=False,
    model_name=None,
):
    if activation not in {None, "after_model", "after_tta", "after_ensemble"}:
        raise KeyError(activation)

    models, loaded_checkpoints = zip(
        *[
            model_from_checkpoint(ck, model_name=model_name, need_embedding=need_embedding, strict=strict)
            for ck in checkpoints
        ]
    )

    required_features = itertools.chain(*[m.required_features for m in models])
    required_features = list(set(list(required_features)))

    if activation == "after_model":
        models = [ApplySigmoidTo(m, output_key=OUTPUT_PRED_MODIFICATION_FLAG, temperature=temperature) for m in models]
        models = [ApplySoftmaxTo(m, output_key=OUTPUT_PRED_MODIFICATION_TYPE, temperature=temperature) for m in models]
        print("Applying sigmoid activation to OUTPUT_PRED_MODIFICATION_FLAG", "after model")
        print("Applying softmax activation to OUTPUT_PRED_MODIFICATION_TYPE", "after model")

    if len(models) > 1:

        model = Ensembler(models, outputs=outputs)
        if activation == "after_ensemble":
            model = ApplySigmoidTo(model, output_key=OUTPUT_PRED_MODIFICATION_FLAG, temperature=temperature)
            model = ApplySoftmaxTo(model, output_key=OUTPUT_PRED_MODIFICATION_TYPE, temperature=temperature)
            print("Applying sigmoid activation to outputs", outputs, "after ensemble")
    else:
        assert len(models) == 1
        model = models[0]

    if tta is not None:
        model = wrap_model_with_tta(model, tta, inputs=required_features, outputs=outputs)
        print("Wrapping models with TTA", tta)

    if activation == "after_tta":
        model = ApplySigmoidTo(model, output_key=OUTPUT_PRED_MODIFICATION_FLAG, temperature=temperature)
        model = ApplySoftmaxTo(model, output_key=OUTPUT_PRED_MODIFICATION_TYPE, temperature=temperature)
        print("Applying sigmoid activation to outputs", outputs, "after TTA")

    return model.eval(), loaded_checkpoints, required_features
