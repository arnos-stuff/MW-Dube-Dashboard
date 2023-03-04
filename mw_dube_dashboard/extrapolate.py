import pandas as pd

import rich
import ray
from ray import tune
from ray.air import RunConfig, ScalingConfig, CheckpointConfig
from ray.train.xgboost import XGBoostTrainer
from ray.tune.tune_config import TuneConfig
from ray.tune.tuner import Tuner

from mw_dube_dashboard.utils import data as datapath, csvFiles, csvMap

def shorten(fname, num_words=4):
    fname = fname.stem
    fname = fname\
        .replace(".", " ")\
        .replace("-", " ")\
        .replace("_", " ")\
        .replace("(", " ")\
        .replace(")", " ")

    fname = [wfn for wfn in fname.split(' ') if wfn.lower() not in ['per', 'of']]
    numwords = min(num_words, len(fname)//2)
    fname = ''.join(map(lambda s: s.capitalize(), fname[:numwords]))
    return fname

def getCommonVals(list1, list2):
    return [val for val in list1 if val in list2]

gendfs = ((shorten(f), pd.read_csv(f)) for f in csvFiles)

def getDataset(name):
    for dfname, df in gendfs:
        if dfname == name:
            return df
        
def preprocessDataset(name):
    df = getDataset(name)
    extra_vars = ['Year']
    cloned_vars = ['Country', 'Decile']
    extra_vars = getCommonVals(extra_vars, df.columns)
    cloned_vars = getCommonVals(cloned_vars, df.columns)
    pred_vars = [var for var in df.columns if var not in extra_vars + cloned_vars]

    dffit = pd.get_dummies(df)
    dfinput = dffit[[c for c in dffit.columns if any(clvar in c for clvar in cloned_vars)]]
    
    datasets = {}
    
    for pvar in pred_vars:
        dfp = dfinput.copy()
        dfp["target"] = dffit[pvar]
        datasets[pvar] = dfp
        
        yield pvar, dfp

datasets = preprocessDataset("LabourWage")

dname, data = next(datasets)

dftrain = ray.data.from_pandas(data)

params = {
    "tree_method": "approx",
    "objective": ["reg:pseudohubererror", "reg:squarederror"],
    "eval_metric": ["mphe", "mae", "rmse", "mape"],
    "num_boost_round": 100,   
}

trainer = XGBoostTrainer(
    scaling_config=ScalingConfig(num_workers=4, _max_cpu_fraction_per_node=0.9),
    label_column="target",
    params=params,
    datasets={"train": dftrain},
    num_boost_round=10,
)

param_space = {
    "eta": tune.loguniform(1e-4, 1e-1),
    "max_depth": tune.randint(1, 9),
    "subsample": tune.uniform(0.5, 1.0),
    "colsample_bytree": tune.uniform(0.5, 1.0),
    "min_child_weight": tune.randint(1, 10),
}

modpath = (datapath / "models" / dname.replace(" ", "-")).as_posix()

tuner = Tuner(
    trainer,
    run_config=RunConfig(
        verbose=1,
        name="xgb-extrapolate",
        local_dir= modpath,
        checkpoint_config=CheckpointConfig(
            num_to_keep=2,
            checkpoint_at_end=True,
        ),  
        ),
    param_space={
        "params": param_space,
    },
    
    tune_config=TuneConfig(
        num_samples=8,
        metric="train-pseudohubererror",
        mode="min",
        scheduler=tune.schedulers.HyperBandScheduler()
    ),
)

results = tuner.fit()

best_result = results.get_best_result()

rich.print(best_result)

dfopt = results.get_dataframe()

rich.print(dfopt)

dfopt.to_csv( data / "models" / dname + "-optimal-params-xgb-extrapolate-results.csv")

# dummyvars = inputmat.drop_duplicates().values
# newYears = np.arange(1980,2022,1)
# dummystacked = np.vstack([dummyvars for _ in newYears ])
# yearstacked = np.array([yr for _ in dummyvars for yr in newYears]).reshape(-1,1)

# Xnew = np.hstack([dummystacked, yearstacked])