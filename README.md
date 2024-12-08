# CORSET: concise and interpretable multi-label rule sets

[CORSET](https://arxiv.org/pdf/2210.01533.pdf) is an algorithm to learn a set of classification rules for multi-label classification problems.


## Environment setup

**our equipment**:

- CPU: i7 10070F 2.90GHz
- Core: 8
- Mem: 65GB

tested only on Linux and Python 3.8.15

**paper equipment**:

- CPU: Xeon E5 2680 v2 2.80 GHz *2
- Core: 10  
- Mem: 256GB

tested only on macOS Monterey and Python 3.8.15

Requirement:

- some compiler for C/C++ programs, e.g., `g++`

Create the virtual environment and install the packages


``` shell
python3 -mvenv .venv
source .venv/bin/activate 
pip install -r requirements.txt
make build
```

To make sure the setup is correct, run the tests:

``` shell
pytest ./tests
```

## An example: training and prediction

``` python
from corset.data import Dataset
from corset.greedy import GreedyCFTPDivMax
from corset.evaluation import Evaluator

# load the data
ds = Dataset(name='medical', datadir="./data", split_train=False)
ds.load()

# initialize the model
clf = GreedyCFTPDivMax(
    min_feature_proba=.8,
    min_label_proba=.8,
    n_tails_per_iter=100,
    n_heads_per_tail=10,
    lambd=10.0,
    n_max_rules=100
)

# fit it
clf.fit(ds.trn_X, ds.trn_Y)

# make predictions
pred_Y = clf.predict(ds.tst_X)

# evaluate the performance
evaluator = Evaluator()
perf = evaluator.report(pred_Y, ds.tst_Y)
print(perf)
# you should get something like:
# OrderedDict([('hamming_accuracy', 0.9889457523029682), ('subset_accuracy', 0.6484135107471852), ('micro_precision', 0.7616300036062027), ('micro_recall', 0.8716467189434586), ('micro_f1', 0.812933025404157), ('macro_precision', 0.8894680208607824), ('macro_recall', 0.5024357158149877), ('macro_f1', 0.4691918958698777)])
```
