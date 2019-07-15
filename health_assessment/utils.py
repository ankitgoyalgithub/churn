from health_assessment.Lib.AutoBinning import AutoBinning
from health_assessment.Lib.KS import KS

def get_insights(data=None, metrics_cols=None, target_col=None, bins_to_try=[3,4,5]):
    best_bin_result_dict={}
    for each in metrics_cols:
        obj=AutoBinning(target_col,each,[3,4,5])
        result_bin,result_threshold=obj.fit(data)
        best_bin_result_dict[each]= result_threshold
        
    ks_output_dict={}
    for each in best_bin_result_dict.keys():
        ksdev,kstable=KS(data.model_status,data[each],bincuts=best_bin_result_dict[each])#bincuts
        kstable['lift']=kstable['dvrate']*1.0/kstable.cumdvrate.values[-1]
        ks_output_dict[each]={'ksvalue':ksdev,'kstable':kstable[['lift']]}
    return ks_output_dict