
from pandas.core.api import Series
from pandas.core.categorical import Categorical
import pandas.core.algorithms as algos
import pandas.core.common as com
import pandas.core.nanops as nanops
from pandas.compat import zip
import numpy as np

def qcutnew(x, q, labels=None, retbins=False, precision=3):
    print(x)
    print(q)
    print(labels)
    print(retbins)
    print(precision)
    if com.is_integer(q):
        quantiles = np.linspace(0, 1, q + 1)
    else:
        quantiles = q
    bins = algos.quantile(x, quantiles)
    return _bins_to_cuts_new(x, bins, labels=labels, retbins=retbins,
                         precision=precision, include_lowest=True)

def _bins_to_cuts_new(x, bins, right=True, labels=None, retbins=False,precision=3, name=None, include_lowest=False):
    x_is_series = isinstance(x, Series)
    series_index = None

    #Added this line to the original code
    bins =np.array(sorted(list(set(bins))))

    if x_is_series:
        series_index = x.index
        if name is None:
            name = x.name

    x = np.asarray(x)

    side = 'left' if right else 'right'
    ids = bins.searchsorted(x, side=side)

    if len(algos.unique(bins)) < len(bins):
        raise ValueError('Bin edges must be unique: %s' % repr(bins))

    if include_lowest:
        ids[x == bins[0]] = 1

    na_mask = com.isnull(x) | (ids == len(bins)) | (ids == 0)
    has_nas = na_mask.any()

    if labels is not False:
        if labels is None:
            increases = 0
            while True:
                try:
                    levels = _format_levels(bins, precision, right=right,
                                            include_lowest=include_lowest)
                except ValueError:
                    increases += 1
                    precision += 1
                    if increases >= 20:
                        raise
                else:
                    break

        else:
            if len(labels) != len(bins) - 1:
                raise ValueError('Bin labels must be one fewer than '
                                 'the number of bin edges')
            levels = labels

        levels = np.asarray(levels, dtype=object)
        np.putmask(ids, na_mask, 0)
        fac = Categorical(ids - 1, levels, ordered=True, fastpath=True)
    else:
        fac = ids - 1
        if has_nas:
            fac = fac.astype(np.float64)
            np.putmask(fac, na_mask, np.nan)

    if x_is_series:
        fac = Series(fac, index=series_index, name=name)

    if not retbins:
        return fac

    return fac, bins


def _format_levels(bins, prec, right=True,
                   include_lowest=False):
    fmt = lambda v: _format_label(v, precision=prec)
    if right:
        levels = []
        for a, b in zip(bins, bins[1:]):
            fa, fb = fmt(a), fmt(b)

            if a != b and fa == fb:
                raise ValueError('precision too low')

            formatted = '(%s, %s]' % (fa, fb)

            levels.append(formatted)

        if include_lowest:
            levels[0] = '[' + levels[0][1:]
    else:
        levels = ['[%s, %s)' % (fmt(a), fmt(b))
                  for a, b in zip(bins, bins[1:])]

    return levels


def _format_label(x, precision=3):
    fmt_str = '%%.%dg' % precision
    if np.isinf(x):
        return str(x)
    elif isinstance(com, float):
        frac, whole = np.modf(x)
        sgn = '-' if x < 0 else ''
        whole = abs(whole)
        if frac != 0.0:
            val = fmt_str % frac

            # rounded up or down
            if '.' not in val:
                if x < 0:
                    return '%d' % (-whole - 1)
                else:
                    return '%d' % (whole + 1)

            if 'e' in val:
                return _trim_zeros(fmt_str % x)
            else:
                val = _trim_zeros(val)
                if '.' in val:
                    return sgn + '.'.join(('%d' % whole, val.split('.')[1]))
                else:  # pragma: no cover
                    return sgn + '.'.join(('%d' % whole, val))
        else:
            return sgn + '%0.f' % whole
    else:
        return str(x)


def _trim_zeros(x):
    while len(x) > 1 and x[-1] == '0':
        x = x[:-1]
    if len(x) > 1 and x[-1] == '.':
        x = x[:-1]
    return x

if __name__=='__main__':
    a, binsofcut = qcutnew(range(25), 3, retbins=True)
    print (a)
    print (binsofcut)

    corner_case = [0]*20+ [val for val in range(20)]

    print ('now testing the corner case', corner_case)
    a1, binsofcut1 = qcutnew(corner_case, 10, retbins=True)

    print (a1)
    print (binsofcut1)

    corner_case_2 = [0] * 20 +[1]

    print('now testing another the corner case', corner_case_2)
    a2, binsofcut2 = qcutnew(corner_case_2, 3, retbins=True)

    print(a2)
    print(binsofcut2)

    print ('End')
