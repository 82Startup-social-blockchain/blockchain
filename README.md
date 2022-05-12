# blockchain

Layer-1 PoS Blockchain to support online social activities

## Overview

- Transactions could define any type of online social activity.

- Blockchain blocks only contain metadata for social transaction. The actual user content is uploaded to external decentralized storage (like IPFS). For this demo, we just store it locally in `storage` folder.

- Use RANDAO to coordinate the consensus process.

- Light node accepts transactions from users and broadcasts to other users. Full node participates in the PoS validation process.

## Get started

1. Clone the repository
2. Set up virtual environment with Python version 3.8 (or above?). Please add the virtualenv directory to .gitignore if you use a different name.

```
$ python -m venv venv
```

3. Activate the virtual environment.

```
$ source venv/bin/activate
```

4. Download the packages. For `cryptography` follow instructions on https://cryptography.io/en/latest/installation/ if you need packages pre-installed.

```
(venv) $ pip install -r requirements.txt
```

5. Run the node locally. You must first set address of the node as an environment variable. You must also set account key file as an environment variable.

If you want to use example data to start with, run

```
(venv) $ python -m example_data.generate_example_data
```

In order to initialize a node with the example data, you need to set an environment `INIT_BLOCKCHAIN_FILE_NAME` with the json file name.

```
(venv) $ python -m genesis.initial_block
(venv) $ export INIT_BLOCKCHAIN_FILE_NAME=blockchain_length2.json # optional
(venv) $ export ACCOUNT_KEY_FILE_NAME=account_0.json
(venv) $ export ADDRESS=http://127.0.0.1:8000
(venv) $ uvicorn runner.main:app --reload --port 8000
```

6. To run tests locally, run

```
(venv) $ python -m unittest discover test/
```

### Points of improvement

- Multiple transactions by same account in one block - make have problem in validation?

### Problems

- Consensus Algorithm

* How does adding randomization work if all nodes need to know which one is the valiator?

- Punishment for troll node

- How to handle account (+stake of the account)

* Do we make account creation part of the blockchain or something different (i.e. account would interact with blockchain just through public key)

- How to prevent timestamp manipulation by a node?

### Plan

1. Put everything in RAM
2. Store everything in Json file
3. Use database to store the blockchain locally (content still in json file)
4. Upload content to S3
