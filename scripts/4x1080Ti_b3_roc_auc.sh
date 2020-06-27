export KAGGLE_2020_ALASKA2=/home/bloodaxe/datasets/ALASKA2

python -m torch.distributed.launch --nproc_per_node=4 train_d_paired.py -m rgb_tf_efficientnet_b3_ns -b 20 -w 6 -d 0.2 -s flat_cos -o Ranger --epochs 50 -a hard\
  --modification-flag-loss roc_auc 1 --modification-type-loss ce 1  -lr 1e-3 --fold 0 --seed 10000 -v --fp16

python -m torch.distributed.launch --nproc_per_node=4 train_d_paired.py -m rgb_tf_efficientnet_b3_ns -b 20 -w 6 -d 0.2 -s flat_cos -o Ranger --epochs 50 -a hard\
  --modification-flag-loss roc_auc 1 --modification-type-loss ce 1  -lr 1e-3 --fold 1 --seed 10001 -v --fp16

python -m torch.distributed.launch --nproc_per_node=4 train_d_paired.py -m rgb_tf_efficientnet_b3_ns -b 20 -w 6 -d 0.2 -s flat_cos -o Ranger --epochs 50 -a hard\
  --modification-flag-loss roc_auc 1 --modification-type-loss ce 1  -lr 1e-3 --fold 2 --seed 10002 -v --fp16

python -m torch.distributed.launch --nproc_per_node=4 train_d_paired.py -m rgb_tf_efficientnet_b3_ns -b 20 -w 6 -d 0.2 -s flat_cos -o Ranger --epochs 50 -a hard\
  --modification-flag-loss roc_auc 1 --modification-type-loss ce 1 -lr 1e-3 --fold 3 --seed 10003 -v --fp16
