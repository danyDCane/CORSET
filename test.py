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