# Publications

1. [Rich Model for Steganalysis of Color Images](http://www.ws.binghamton.edu/fridrich/Research/color-04.pdf)
2. [The ALASKA Steganalysis Challenge: A First Step Towards Steganalysis ”Into The Wild”](https://hal.archives-ouvertes.fr/hal-02147763/document)
3. [Rich Models for Steganalysis of Digital Images](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.441.6997&rep=rep1&type=pdf)
4. [Pixels-off: Data-augmentation Complementary Solution for Deep-learning Steganalysis](https://hal-lirmm.ccsd.cnrs.fr/lirmm-02559838/file/IHMMSec-2016_Yedroudj_Chaumont_Comby_Amara_Bas_Pixels-off.pdf)

# Useful

1. https://www.kaggle.com/remicogranne/jpeg-explanations
2. https://github.com/digantamisra98/EvoNorm/blob/master/evonorm2d.py
3. https://github.com/Steganalysis-CNN/residual-steganalysis/blob/master/init/res_finetune_test.m
4. https://github.com/yedmed/steganalysis_with_CNN_Yedroudj-Net/blob/master/pytorch_version/Covariance_Pooling_Steganalytic_Network_cat.py

https://github.com/facebookresearch/detr/tree/master/models
https://www.youtube.com/watch?v=v8U9mM1Vwv0
https://github.com/mahyarnajibi/FreeAdversarialTraining/blob/master/configs.yml
https://github.com/TAMU-VITA/Adv-SS-Pretraining/tree/master/pretraining

# Models

|Experiment Name                               | Model                  | Fold | bAUC | cAUC | Acc01 | LB    | LB (Flip) | LB (D4) |
|----------------------------------------------|------------------------|------|------|------|-------|-------|-----------|---------|
| May07_16_48_rgb_resnet34_fold0               | rgb_resnet34           | 0    | 8449 |      | 56.97 | 
| May07_16_48_rgb_resnet34_fold0 (fine-tune)   | rgb_resnet34           | 0    | 8451 |      | 56.90 |
| May08_22_42_rgb_resnet34_fold1               | rgb_resnet34           | 1    | 8439 |      | 56.62 |
| May09_15_13_rgb_densenet121_fold0_fp16       | rgb_densenet121        | 0    | 8658 | 8660 | 60.90 |
| May11_08_49_rgb_densenet201_fold3_fp16       | rgb_densenet201        | 3    | 8402 | 8405 | 56.38 |
|----------------------------------------------|------------------------|------|------|------|-------|-----|-----------|---------|
| May13_23_00_rgb_skresnext50_32x4d_fold0_fp16 | rgb_skresnext50_32x4d  | 0    | 9032 | 9032 | 67.22 |
| May13_19_06_rgb_skresnext50_32x4d_fold1_fp16 | rgb_skresnext50_32x4d  | 1    | 9055 | 9055 | 67.60 |
| May12_13_01_rgb_skresnext50_32x4d_fold2_fp16 | rgb_skresnext50_32x4d  | 2    | 9049 | 9048 | 67.56 |
| May11_09_46_rgb_skresnext50_32x4d_fold3_fp16 | rgb_skresnext50_32x4d  | 3    | 8700 | 8699 | 61.45 |
|----------------------------------------------|------------------------|------|------|------|-------|-------|-------|-------|
| May15_17_03_ela_skresnext50_32x4d_fold1_fp16 | ela_skresnext50_32x4d     | 1    | 9144 | 9144 | 69.55 | 0.915 | 0.919 | 0.919 |
| May21_13_28_ela_skresnext50_32x4d_fold2_fp16 | ela_skresnext50_32x4d     | 2    | 9164 | 9163 | 70.17 | 0.921 | 0.921
| May24_11_08_ela_skresnext50_32x4d_fold0_fp16 | ela_skresnext50_32x4d     | 0    |
| May26_12_58_ela_skresnext50_32x4d_fold3_fp16 | ela_skresnext50_32x4d     | 3    |      |      |       | 0.922
|------------------------------------------------|-------------------------|------|------|------|-------|-------|-------|-------|
| May18_20_10_ycrcb_skresnext50_32x4d_fold0_fp16 | ycrcb_skresnext50_32x4d | 0    | 8266 | 8271 | 55.34 | 
|------------------------------------------------|-------------------------|------|------|------|-------|-------|-------|-------|
| May28_13_04_rgb_tf_efficientnet_b6_ns_fold0    | rgb_tf_efficientnet_b6  | 0    |      |      |       | 0.917 |
| May28_18_49_rgb_tf_efficientnet_b6_ns_fold1    | rgb_tf_efficientnet_b6  | 1    |      |      |       | 0.923

# Models (New folds, Holdout)

## rgb_tf_efficientnet_b6_ns

|----------------------------------------------|-----------------------------|------|--------|--------|--------|-------|-------|-----------|---------|
|Experiment Name                               | Model                       | Fold | Metric | bAUC   | cAUC   | Acc01 | LB    | LB (Flip) | LB (D4) |
|----------------------------------------------|-----------------------------|------|--------|--------|--------|-------|-------|-----------|---------|
| Jun05_08_49_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 0    | loss   | 0.9199 | 0.9200 | 71.36 |
| Jun05_08_49_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 0    | b-auc  | 0.9205 | 0.9205 | 70.93 |
| Jun05_08_49_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 0    | c-auc  | 0.9205 | 0.9205 | 70.93 |
|----------------------------------------------|-----------------------------|------|--------|--------|--------|-------|-------|-----------|---------|
| Jun09_16_38_rgb_tf_efficientnet_b6_ns *      | rgb_tf_efficientnet_b6_ns   | 1    | loss   | 0.9237 | 0.9238 | 72.29 |
| Jun09_16_38_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 1    | b-auc  | 0.9237 | 0.9238 | 72.29 |
| Jun09_16_38_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 1    | c-auc  | 0.9237 | 0.9238 | 72.29 |
|----------------------------------------------|-----------------------------|------|--------|--------|--------|-------|-------|-----------|---------|
| Jun11_08_51_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 2    | loss   | 
| Jun11_08_51_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 2    | b-auc  | 
| Jun11_08_51_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 2    | c-auc  | 
|----------------------------------------------|-----------------------------|------|--------|--------|--------|-------|-------|-----------|---------|
| Jun10_08_49_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 3    | loss   | 
| Jun10_08_49_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 3    | b-auc  | 
| Jun10_08_49_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 3    | c-auc  | 
|----------------------------------------------|-----------------------------|------|--------|--------|--------|-------|-------|-----------|---------|
| Jun18_19_24_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 0    | loss   | 0.9264 | 0.9254 | 72.33 |       |
| Jun18_19_24_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 0    | b-auc  | 0.9265 | 0.9253 | 72.08 |       | 0.926 / 0.924 |    |
| Jun18_19_24_rgb_tf_efficientnet_b6_ns        | rgb_tf_efficientnet_b6_ns   | 0    | c-auc  | 0.9264 | 0.9254 | 72.33 |       | 0.923 / 0.922 |    |
|----------------------------------------------|-----------------------------|------|--------|--------|--------|-------|-------|-----------|---------|


Average of 4 folds (best loss): 
Average of 4 folds (best auc b): 
Average of 4 folds (best auc c): 
Average of 4 folds (average of all 3): 

#

https://github.com/YangzlTHU/IStego100K
https://arxiv.org/pdf/1911.05542.pdf