import math
import numpy as np
import random 
from health_assessment.Lib.KS import KS

class AutoBinning(object):
    def __init__(self, target, metric_col, bin_range, min_ks=5, random_iterations=10, max_iter_to_converge=30,
                 max_bins_for_thresholds=1000, min_ratio_on_evidence_for_complex_model=3):
        self.target = target
        self.metric_col = metric_col
        self.bin_range = bin_range
        self.min_ks = min_ks
        self.random_iterations = random_iterations
        self.max_iter_to_converge = max_iter_to_converge
        self.result_dict = {}
        self.max_bins_for_thresholds = max_bins_for_thresholds
        self.min_ratio_on_evidence_for_complex_model = min_ratio_on_evidence_for_complex_model
        self.all_thresholds = []

        if self.max_bins_for_thresholds is None:
            self.max_bins_for_thresholds = int(metric_col.nunique() / 2.0)
        assert len(bin_range) > 0

    def make_all_possible_thresholds(self, data):
        if data[self.metric_col].nunique() <= 10:
            self.all_thresholds = [-1 * float('inf')] + list(data[self.metric_col].unique()) + [float('inf')]
        else:
            _, _, self.all_thresholds = KS(labelCol=data[self.target], predictedCol=data[self.metric_col],
                                           nBins=self.max_bins_for_thresholds, retBins=True)
        self.all_thresholds = sorted(self.all_thresholds)

    @staticmethod
    def find_middle(inplist):
        # returns the middle element if the list has odd length and mean of the two middle elements otherwise
        assert len(inplist) > 0
        len_here = len(inplist)
        if len_here % 2 == 0:
            return (inplist[int(len_here / 2) - 1] + inplist[int(len_here / 2)]) / 2
        else:
            return inplist[int(len_here / 2)]

    def find_potential_thresholds(self, lower_exclusive_threshold, upper_inclusive_threshold):
        return sorted([each_th for each_th in self.all_thresholds if
                       lower_exclusive_threshold <= each_th <= upper_inclusive_threshold])

    def default_threshold(self, inpdata, lower_value, upper_value):
        subset_data = inpdata[(inpdata[self.metric_col] > lower_value) & (inpdata[self.metric_col] <= upper_value)]
        potential_thresholds = self.find_potential_thresholds(lower_exclusive_threshold=lower_value,
                                                              upper_inclusive_threshold=upper_value)
        if len(potential_thresholds) == 3:
            return potential_thresholds[1]
        # finding the median in the data
        median_metric = subset_data[self.metric_col].median()
        if median_metric == lower_value:
            bin_cut_threshold = potential_thresholds[1]
        elif median_metric == upper_value:
            bin_cut_threshold = potential_thresholds[-2]
        else:
            bin_cut_threshold = median_metric
        return bin_cut_threshold

    def get_best_split_threshold(self, data, lower_threshold_input, upper_threshold_input):
        renewal_actual = data[self.target]
        bincuts_for_ks = self.find_potential_thresholds(lower_exclusive_threshold=lower_threshold_input,
                                                        upper_inclusive_threshold=upper_threshold_input)
        if data[self.target].nunique() == 1:
            bin_cut_threshold = self.default_threshold(data, lower_value=lower_threshold_input,
                                                       upper_value=upper_threshold_input)
        elif data[self.metric_col].nunique() == 1:
            bin_cut_threshold = data[self.metric_col].unique()[0]

        else:
            print('*****************************************')
            print(renewal_actual.value_counts())
            print(data[self.metric_col].value_counts()) 
            print(bincuts_for_ks)
            print('*****************************************')
            ksdev, kstable = KS(renewal_actual, data[self.metric_col], bincuts=bincuts_for_ks)
            if abs(ksdev) >= self.min_ks:
                bin_cut_threshold = kstable.ix[abs(kstable.KS).idxmax()]['minScore']

            else:
                bin_cut_threshold = self.default_threshold(data, lower_value=lower_threshold_input,
                                                           upper_value=upper_threshold_input)
        return bin_cut_threshold

    def get_subset_data(self, data, lower_end, upper_end):
        subset_data = data[(data[self.metric_col] > lower_end) & (data[self.metric_col] <= upper_end)].copy()
        return subset_data

    def get_thresholds(self, no_of_bins):
        thresholds = []
        thresholds.append(-np.inf)
        if no_of_bins != 1:
            temp = self.all_thresholds[1:-1]
            thresholds += random.sample(list(temp), no_of_bins - 1)
        thresholds.append(np.inf)
        return sorted(thresholds)

    def adjust_thresholds(self, data, initial_threshold_set):
        bins = []
        for each_index in range(1, len(initial_threshold_set) - 1):
            lower_threshold = initial_threshold_set[each_index - 1]
            upper_threshold = initial_threshold_set[each_index + 1]
            subset_data = self.get_subset_data(data, initial_threshold_set[each_index - 1],
                                               initial_threshold_set[each_index + 1])
            bin_cut_threshold = self.get_best_split_threshold(subset_data, lower_threshold, upper_threshold)
            initial_threshold_set[each_index] = bin_cut_threshold
            bins.append(bin_cut_threshold)
        new_thresholds = list()
        new_thresholds.append(-np.inf)
        new_thresholds.extend(bins)
        new_thresholds.append(np.inf)
        return new_thresholds

    def converged_threshold(self, data, new_threshold_set):
        run_dict = {}
        for i in range(self.max_iter_to_converge):
            run_dict[i] = new_threshold_set
            if i > 1 and run_dict[i] == run_dict[i - 1]:
                break
            else:
                new_threshold_set = self.adjust_thresholds(data, new_threshold_set)
        return run_dict[list(run_dict.keys())[-1]]

    def best_threshold_of_n_bins(self, data, no_of_bins):
        iter_threshold_map = {}
        all_best_splits = {}
        for each_iter in range(1, self.random_iterations + 1):
            iter_threshold_map[each_iter] = self.get_thresholds(no_of_bins)
            temp_threshold_set = iter_threshold_map[each_iter][:]
            all_best_splits[each_iter] = self.converged_threshold(data, temp_threshold_set)
        unique_best_split = {}
        for key, value in all_best_splits.items():
            if value not in unique_best_split.values():
                unique_best_split[key] = value
        return iter_threshold_map, unique_best_split

    @staticmethod
    def beta_fn_log(a, b):
        agamma = math.lgamma(a)
        bgamma = math.lgamma(b)
        abgamma = math.lgamma(a + b)
        diff = agamma + bgamma - abgamma
        return diff

    def check_evidence_ratio_of_beta_log(self, simple_champion_log_beta, complex_challenger_log_beta):
        actual_ratio = np.exp(complex_challenger_log_beta - simple_champion_log_beta)
        return True if actual_ratio >= self.min_ratio_on_evidence_for_complex_model else False

    def get_beta_value_log(self, data, split_bin):
        split_bin = np.sort(list(set(split_bin)))
        ksdev, kstable = KS(data[self.target], data[self.metric_col], bincuts=split_bin)  # bincuts
        beta_log_value = []
        for i in range(kstable.shape[0]):
            beta_log = self.beta_fn_log(kstable[0].values[i] + 1, kstable[1].values[i] + 1)
            beta_log_value.append(beta_log)
        return np.sum(beta_log_value)

    def best_random_split_iteration(self, data, all_best_splits):
        best_split = all_best_splits[1]
        max_beta_value = self.get_beta_value_log(data, all_best_splits[1])
        for each_split in list(all_best_splits.keys())[1:]:
            total_beta_value = self.get_beta_value_log(data, all_best_splits[each_split])
            if max_beta_value < total_beta_value:
                max_beta_value = total_beta_value
                best_split = all_best_splits[each_split]
        return best_split

    def make_default_result_dict(self, which_default_value=0.5):
        return {
            self.metric_col: [{'left': -1 * float('inf'), 'right': float('inf'),'value': which_default_value}]
        }

    def fit(self, data):
        # handling special cases
        # number of bins being tried cannot be more than the unique values in the metric col
        if data.empty:
            self.result_dict = self.make_default_result_dict()
            best_bin = 1
            best_threshold = [-1 * (float('inf')), float('inf')]
            return best_bin, best_threshold
        uniq_values_in_train = data[self.metric_col].nunique()
        self.bin_range = list(set((range(uniq_values_in_train + 1))).intersection(set(self.bin_range + [1])))
        if data[self.target].nunique() == 1:
            self.result_dict = self.make_default_result_dict(which_default_value=data[self.target].iloc[0])
            best_bin = 1
            best_threshold = [-1 * float('inf'), float('inf')]
            return best_bin, best_threshold
        elif data[self.target].nunique() == 0:
            return None
        self.make_all_possible_thresholds(data)
        # dropping the bin ranges which are not possible in training data
        self.bin_range = sorted([eachbin for eachbin in self.bin_range if eachbin < len(self.all_thresholds)])
        bin_level_best_split = {}
        beta_log_dict = {}
        best_bins = None
        for current_bins in sorted(self.bin_range):
            all_thresholds_dict, best_split_dict = self.best_threshold_of_n_bins(data, current_bins)
            bin_level_best_split[current_bins] = self.best_random_split_iteration(data, best_split_dict)
            beta_log_dict[current_bins] = self.get_beta_value_log(data, bin_level_best_split[current_bins])
            if best_bins is None:
                best_bins = current_bins
            else:
                if self.check_evidence_ratio_of_beta_log(simple_champion_log_beta=beta_log_dict[best_bins],
                                                         complex_challenger_log_beta=beta_log_dict[current_bins]):
                    best_bins = current_bins

        best_threshold = bin_level_best_split[best_bins]

        ksdev, kstable = KS(data[self.target], data[self.metric_col], bincuts=best_threshold)
        trained_threshold_dict = kstable[['dvrate']].to_dict()['dvrate']
        temp_list = []
        for interval in trained_threshold_dict:
            temp_list.append({'left': interval.left, 'right': interval.right,
                              'value': trained_threshold_dict[interval]})
        self.result_dict[self.metric_col] = temp_list
        return best_bins, best_threshold
