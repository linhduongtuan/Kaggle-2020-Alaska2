export KAGGLE_2020_ALASKA2=/data/alaska2

python -m torch.distributed.launch --nproc_per_node=4 train_d.py -m rgb_tf_efficientnet_b7_ns -b 10 -w 6 -d 0.2 -s cos -o fused_sgd --epochs 50 -a medium\
  --modification-flag-loss bce 1 --modification-type-loss ce 1 -lr 1e-2 -wd 1e-4 --fold 0 --seed 10 -v --fp16 --obliterate 0.05

python -m torch.distributed.launch --nproc_per_node=4 train_d.py -m rgb_tf_efficientnet_b7_ns -b 10 -w 6 -d 0.2 -s cos -o fused_sgd --epochs 50 -a medium\
  --modification-flag-loss bce 1 --modification-type-loss ce 1 -lr 1e-2 -wd 1e-4 --fold 1 --seed 20 -v --fp16 --obliterate 0.05

python -m torch.distributed.launch --nproc_per_node=4 train_d.py -m rgb_tf_efficientnet_b7_ns -b 10 -w 6 -d 0.2 -s cos -o fused_sgd --epochs 50 -a medium\
  --modification-flag-loss bce 1 --modification-type-loss ce 1 -lr 1e-2 -wd 1e-4 --fold 2 --seed 30 -v --fp16 --obliterate 0.05

python -m torch.distributed.launch --nproc_per_node=4 train_d.py -m rgb_tf_efficientnet_b7_ns -b 10 -w 6 -d 0.2 -s cos -o fused_sgd --epochs 50 -a medium\
  --modification-flag-loss bce 1 --modification-type-loss ce 1 -lr 1e-2 -wd 1e-4 --fold 3 --seed 40 -v --fp16 --obliterate 0.05
