# nch-faucet

## server side

```
# get source code
cd <working_dir>
git clone https://github.com/iavl/nch-faucet.git && cd nch-faucet

# start redis
redis-server &

# start clfacet.py
python clfaucet.py 1>result.log 2>&1 &
```

## client side

```
# you can get 100 tokens each call and max 2000 tokens per day.
curl http://<your_server_ip>/get_token?<nch_address>
```
