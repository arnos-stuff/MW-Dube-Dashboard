import pandas as pd
import numpy as np
import patsy as pt
import statsmodels.api as sm
import statsmodels.formula.api as smf

from itertools import product

from mw_dube_dashboard.utils import data, csvFiles, csvMap

__all__ = ['make']

def cartesian_product(*arrays):
    broadcastable = np.ix_(*arrays)
    broadcasted = np.broadcast_arrays(*broadcastable)
    rows, cols = np.prod(broadcasted[0].shape), len(broadcasted)
    dtype = np.result_type(*arrays)

    out = np.empty(rows * cols, dtype=dtype)
    start, end = 0, rows
    for a in broadcasted:
        out[start:end] = a.reshape(-1)
        start, end = end, end + rows
    return out.reshape(cols, rows).T

def shorten(fname):
    return "-".join(fname.stem.split('-')[:2])

def toFormulaColumn(colname):
    return colname.replace(' ', '_')\
        .replace('-', '_')\
        .replace('%', 'pct')\
        .replace('(', 'openbracket')\
        .replace(')', 'closebracket')\
        .replace('?', 'qmark')\
        .replace('$', 'dollarsign')\
        .replace('.', '_dot_')\
        .replace(' ', '')

def fromFormulaColumn(colname):
    return colname.replace('_', ' ')\
        .replace('pct', '%')\
        .replace('openbracket', '(')\
        .replace('closebracket', ')')\
        .replace('qmark', '?')\
        .replace('dollarsign', '$')\
        .replace('_dot_', '.')

def castDF(df):
    for c in df.columns:
        firstval = df[c].iloc[0]
        if isinstance(firstval, str):
            try:
                df[c] = df[c].astype(float, errors='raise')
            except ValueError:
                df[c] = df[c].astype(str)
        else:
            df[c] = df[c].astype(float)
    return df

def getCommonVals(list1, list2):
    return [val for val in list1 if val in list2]

def extrapolate(df, intervals=None):
    if intervals is None:
        intervals = {'Year': (1980, 2020)}
    extra_vars = ['Year']
    cloned_vars = ['Country', 'Decile']
    extra_vars = getCommonVals(extra_vars, df.columns)
    cloned_vars = getCommonVals(cloned_vars, df.columns)
    pred_vars = [var for var in df.columns if var not in extra_vars + cloned_vars]

    dffit = pd.get_dummies(df)
    inputmat = dffit[[c for c in dffit.columns if any(clvar in c for clvar in cloned_vars)]]
    dummyvars = inputmat.drop_duplicates().values
    newYears = np.arange(1980,2022,1)
    dummystacked = np.vstack([dummyvars for _ in newYears ])
    yearstacked = np.array([yr for _ in dummyvars for yr in newYears]).reshape(-1,1)

    Xnew = np.hstack([dummystacked, yearstacked])

    for var in pred_vars:
        mod = sm.OLS(
            dffit[var],
            dffit[[c for c in dffit.columns if "wage" not in c.lower()]],
        )
                

    cloned_vars = [var for var in cloned_vars if var in df.columns]

    extrapolated = [
        np.arange(*intervals[var], 1).astype(float)
        if var in intervals
        else np.arange(df[var].min(), df[var].max(), 1)
        for var in extra_vars
    ]
    cloned = [
        df[var].astype(str).unique() for var in cloned_vars
    ]

    prodvars = cartesian_product(*extrapolated, *cloned)

    dfprod = pd.DataFrame(prodvars, columns=inputvars)

    dfprod = castDF(dfprod)

    dfext = pd.merge(dfprod, df, on=inputvars, how='outer')

    valuecols = [col for col in df.columns if col not in inputvars]

    dfext = dfext.sort_values(by=inputvars)

    dfext.loc[:,valuecols].interpolate(
        method='cubic', axis=0,
        limit_direction='both',
        inplace=True,
        limit=len(dfext) // 2
        )

    return dfext
    
    
    

def make():
    gendfs = ((shorten(f), pd.read_csv(f)) for f in csvFiles)

    start_prefix, curdf = next(gendfs)
    curdf = extrapolate(curdf)
    start = True

    while True:
        try:
            prefix, nextdf = next(gendfs)
            nextdf = extrapolate(nextdf)
        except StopIteration:
            break

        if start:
            start = False
            left_suffix = f"-{start_prefix}"
        else:
            left_suffix = ""

        curdf = curdf.merge(nextdf, on=['Country', 'Year'], suffixes=(left_suffix, f"-{prefix}"))

    # interpolate missing values
    
    curdf = extrapolate(curdf)

    # postprocessing

    relative_cols = [col for col in curdf.columns if 'share' in col.lower()]
    gdp_col = [
        col
        for col in curdf.columns
        if 'gdp' in col.lower() and '%' not in col.lower()
    ].pop()
    population_col = [col for col in curdf.columns if 'population' in col.lower()].pop()
    labour_income_col = [col for col in curdf.columns if 'labour income' in col.lower()].pop()
    working_population_col = [col for col in curdf.columns if 'participation rate' in col.lower()].pop()

    for col in relative_cols:
        abscol = col.lower().replace('share', 'total').capitalize()
        curdf[abscol] = (curdf[col].astype(float) / 100.0) * curdf[gdp_col].astype(float)
        avgcol = col.lower().replace('share', 'average').capitalize()
        # compute average income
        popwork = curdf[population_col].astype(float) * curdf[working_population_col].astype(float) / 100.0
        totalincome = curdf[labour_income_col] * popwork
        multiplier = 10.0 if 'decile' in col.lower() else 25.0 if 'quintile' in col.lower() else 25.0
        curdf[avgcol] = multiplier * totalincome / popwork

    curdf.to_csv(data / 'processed' / 'Wage-Data-Full.csv', index=False)

    return curdf
    
        