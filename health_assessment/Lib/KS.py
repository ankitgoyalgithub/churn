import pandas as pd
from health_assessment.Lib.bins import qcutnew


def KS(
    labelCol,
    predictedCol,
    nBins=10,
    retBins=False,
    bincuts=False,
    binlabels=None,
    discretelimit=10,
):
    """Returns the KS Statistic of the given predicted probabilities and labels
    binlabels: Used as labels for the resulting bins. Must be of the same length as the resulting bins.
    """
    assert len(labelCol) == len(predictedCol)
    assert labelCol.ndim == predictedCol.ndim
    assert set(labelCol) in [set([0, 1])]
    inpDF = pd.DataFrame({"Label": labelCol, "Predicted": predictedCol})

    # checking if the distinct values are less than 10
    if bincuts is False:
        assert inpDF["Predicted"].min() != inpDF["Predicted"].max()
        dispredvalues = inpDF["Predicted"].nunique()

        if discretelimit is not None and dispredvalues <= discretelimit:
            bincuts = [-1 * float("inf")] + list(inpDF["Predicted"].unique())
            bincuts = sorted(list(set(bincuts)))
            bincuts[-1] = float("inf")
            inpDF["bin"], binsofcut = pd.cut(
                inpDF["Predicted"], bins=bincuts, retbins=True, labels=binlabels
            )
        else:
            inpDF["bin"], binsofcut = qcutnew(inpDF["Predicted"], nBins, retbins=True)
            binsofcut[0] = -1 * float("inf")
            binsofcut[-1] = float("inf")
    else:
        inpDF["bin"], binsofcut = pd.cut(
            inpDF["Predicted"], bins=bincuts, retbins=True, labels=binlabels
        )
    ksTable = pd.crosstab(inpDF["bin"], inpDF["Label"])
    ksTable["minScore"] = binsofcut[:-1]
    ksTable["maxScore"] = binsofcut[1:]
    ksTable.sort_values(by="minScore", ascending=False, inplace=True)
    ksTable["cumonespct"] = ksTable[1].cumsum() / ksTable[1].sum()
    ksTable["cumzerospct"] = ksTable[0].cumsum() / ksTable[0].sum()
    ksTable["dvrate"] = ksTable[1] / (ksTable[0] + ksTable[1])
    ksTable["cumdvrate"] = ksTable[1].cumsum() / (
        ksTable[1].cumsum() + ksTable[0].cumsum()
    )
    baseRate = ksTable.cumdvrate[-1]
    ksTable["lift"] = ksTable["dvrate"] / baseRate
    ksTable["KS"] = (ksTable["cumonespct"] - ksTable["cumzerospct"]) * 100.0
    if retBins:
        return max(ksTable.KS, key=abs), ksTable, binsofcut
    else:
        return max(ksTable.KS, key=abs), ksTable


def tableFormatter(inpksTable):
    newTable = inpksTable.copy()
    for col in [
        "minScore",
        "maxScore",
        "cumonespct",
        "cumzerospct",
        "dvrate",
        "cumdvrate",
    ]:
        newTable[col] = newTable[col].apply("{0:.2}".format)
    newTable["KS"] = newTable["KS"].map(lambda x: round(x, 1))
    return newTable


def KSBestSplitThreshold(labels, predictions, retBins=False):
    maxKS, ksTable = KS(labels, predictions, nBins=40)
    scoreCutoff = ksTable.loc[ksTable.KS == maxKS, "minScore"][0]
    if retBins:
        return scoreCutoff, [-np.Inf, scoreCutoff, np.Inf]
    else:
        return scoreCutoff
