export KAGGLE_2020_ALASKA2=/data/alaska2

python -m torch.distributed.launch --nproc_per_node=4 train_d.py -m rgb_tf_efficientnet_b6_ns -b 12 -w 6 -d 0.2 -s cos -o fused_sgd --epochs 50 -a medium\
  --modification-flag-loss bce 1 --modification-type-loss ce 1 -lr 1e-2 -wd 1e-4 --fold 3 --seed 10003 -v --fp16 -nid /data/mirflickr --obliterate 0.05