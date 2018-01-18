#!/bin/bash

# Because I'm too lazy to figure out how to make more uniformly random
# partitions, I futz with rng seeds until they reliably reproduce something nice.
mkdir -p fake

# Really simple, 2-cluster datasets starting at 
echo "20x10"
python gen_fake_data.py -SO -r 20 -c 10 2 --rng_seed 7
python gen_fake_data.py -SO -r 20 -c 10 4 --rng_seed 0
echo "200x10"
python gen_fake_data.py -SO -r 200 -c 10 2 --rng_seed 0
python gen_fake_data.py -SO -r 200 -c 10 4 --rng_seed 0
python gen_fake_data.py -SO -r 200 -c 10 8 --rng_seed 0
echo "200x100"
python gen_fake_data.py -SO -r 200 -c 100 2 --rng_seed 0
python gen_fake_data.py -SO -r 200 -c 100 4 --rng_seed 0
python gen_fake_data.py -SO -r 200 -c 100 8 --rng_seed 0
echo "2000x10"
python gen_fake_data.py -SO -r 2000 -c 10 2 --rng_seed 0
python gen_fake_data.py -SO -r 2000 -c 10 4 --rng_seed 0
python gen_fake_data.py -SO -r 2000 -c 10 8 --rng_seed 0
echo "2000x100"
python gen_fake_data.py -SO -r 2000 -c 100 2 --rng_seed 0
python gen_fake_data.py -SO -r 2000 -c 100 8 --rng_seed 0
python gen_fake_data.py -SO -r 2000 -c 100 20 --rng_seed 0

echo "Increasing noise parameters for vn-size datasets."
RWS=6334
CLS=285
declare -a arr=("0.0" "0.01" "0.05" "0.1" "0.2" "0.4")

for i in "${arr[@]}"; do
    echo "$RWS x $CLS noise $i"
    # I don't save the image, for time reasons
    python gen_fake_data.py -O -r "$RWS" -c "$CLS" -e "$i" --rng_seed 0 20
done
