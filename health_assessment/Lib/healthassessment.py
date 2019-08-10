import pandas as pd
import numpy as np
import math
import random
import datetime as dt

class HealthAssessment:
    def __init__(self, ID, target, churn_date, snapshot_date, target_window=8, metrics_col=[]):
        self.use_case = 'Gainsight'
        self.ID = ID
        self.target = target
        self.scoringDate = 'score_week'
        self.churn_date = churn_date
        self.snapshot_date = snapshot_date
        self.target = target
        self.target_window = target_window
        self.score_col = metrics_col
        self.score_col.extend([self.ID, self.snapshot_date])  # .extend(self.col_list)

    def available_data(self, data, date_col, period=12):
        data[date_col] = pd.to_datetime(data[date_col])
        data['year'] = data[date_col].dt.year
        data['month'] = data[date_col].dt.month
        data[date_col] = pd.to_datetime(data[date_col])
        start_date = max(data[date_col]) - dt.timedelta(period * 365 / 12)
        data = data[data[date_col] >= start_date]
        data = data.groupby(['year', 'month']).count()
        return data

    def get_outcome_timeline(self,outcome_data, churn_date, period=12):
        outcome_data[self.churn_date] = pd.to_datetime(outcome_data[self.churn_date])
        outcome_data['year'] = outcome_data[churn_date].dt.year
        outcome_data['month'] = outcome_data[churn_date].dt.month
        outcome_data.sort_values(['year', 'month'], inplace=True)
        return outcome_data.groupby(['year', 'month', 'Status']).count()[[self.ID]].tail(period)

    def preprocess_data(self, outcome, score_history, company):
        # preprocess account outcome data
        if self.use_case == 'Gainsight':
            company[self.ID] = company['sfdc account id'].apply(lambda x: x[:-3] if len(x) == 18 else x)
        outcome = outcome[[self.ID, self.churn_date, self.target]]
        outcome.drop_duplicates(inplace=True)
        # preprocess history
        score_history.rename(
            columns={'Scorecard Id': 'scorecard id', 'Company Id': 'account_id', 'Created Date': 'created_date'},
            inplace=True)
        history_with_SFDCid = company[[self.ID, 'scorecard id', 'gsid']].merge(score_history, how='inner',
                                                                               left_on=['scorecard id', 'gsid'],
                                                                               right_on=['scorecard id', 'account_id'])
        history_with_SFDCid = history_with_SFDCid[self.score_col]
        history_status = history_with_SFDCid.merge(outcome, how='inner', on=self.ID)
        history_status[self.snapshot_date] = pd.to_datetime(history_status[self.snapshot_date])
        return history_status

    # Generate Time series entries( Kind of etdata concept for given peirod of time)
    def create_account_date_set(self, data, start, end, intervals=52):
        begin = dt.datetime.strptime(start, "%Y-%m-%d").date()
        begin = begin + dt.timedelta(days=-begin.weekday())
        last = dt.datetime.strptime(end, "%Y-%m-%d").date()
        last = last + dt.timedelta(days=-last.weekday())
        date_list = []
        delta = (last - begin) / intervals
        for i in range(1, intervals + 1):
            date_list.append((begin + i * delta).strftime('%Y-%m-%d'))
        print(len(date_list))
        print(data.shape)
        week_ids = pd.DataFrame(
            {self.ID: sorted((list(data[self.ID])) * intervals), 'score_week': date_list * data[self.ID].nunique()})
        week_ids['score_week'] = pd.to_datetime(week_ids['score_week'])
        return week_ids

    # TODO:
    # This method needs to be relaced by simply shifting all the dates to its corresponding start or end of the week
    # In both the data sets then simply join on ID and date column.

    def merge_data(self, etdata_sample, history):
        etdata_sample[self.scoringDate] = pd.to_datetime(etdata_sample[self.scoringDate])
        history[self.snapshot_date] = pd.to_datetime(history[self.snapshot_date])
        etdata_sample['year'] = etdata_sample[self.scoringDate].dt.year
        etdata_sample['week'] = etdata_sample[self.scoringDate].dt.week
        history['year'] = history[self.snapshot_date].dt.year
        history['week'] = history[self.snapshot_date].dt.week
        final_set = etdata_sample.merge(history, on=[self.ID, 'year', 'week'])
        return final_set

    def get_model_status(self, data, score_week, churn_col):
        x = data[score_week] - data[churn_col]
        data['week_advance'] = x / np.timedelta64(1, 'W')
        data = data[data['week_advance'] < 0].copy()
        data['model_status'] = data['week_advance'].apply(lambda x: 'Active' if x <= -(self.target_window) else 'Churn')
        return data

    def run_health_assessment(self, history_status):
        history_status[self.snapshot_date] = pd.to_datetime(history_status[self.snapshot_date])
        etdata_sample = history_status[[self.ID]]
        etdata_sample.drop_duplicates(inplace=True)
        sample_set = self.create_account_date_set(etdata_sample, str(history_status[self.snapshot_date].min().date()),
                                                  str(history_status[self.snapshot_date].max().date()))
        final_data = self.merge_data(sample_set, history_status)
        final_data[self.churn_date] = pd.to_datetime(final_data[self.churn_date])
        final_data[self.scoringDate] = pd.to_datetime(final_data[self.scoringDate])
        model_record = self.get_model_status(final_data, self.scoringDate, self.churn_date)
        model_record = model_record[
            model_record.week_advance.apply(lambda x: True if abs(x) > (self.target_window - 1) else False)].copy()
        return model_record


if __name__ == '__main__':
    data_dir = '/Users/mkumar/Desktop/health_assessment/'
    outcome_data = pd.read_csv(data_dir + 'outcome_data.csv', encoding="cp1252")
    # history=pd.read_csv(data_dir+'sc_account_history_a964b2f6fc254946a1ca8f9838f8045f.csv')
    history = pd.read_csv(data_dir+'history_2000.csv', encoding="cp1252")
    company = pd.read_csv(data_dir + 'company.csv', encoding="cp1252")
    obj = HealthAssessment(ID='Account ID', churn_date='Inactivation Date',
                           snapshot_date='Snapshot Date', target='Status', metrics_col=["Create Offer Tool",
                                                                                        "Lost Sales", "Last Visit",
                                                                                        "Opinion Scores", "GM Tenure",
                                                                                        "Billing", "CSM Opinion",
                                                                                        "CSS Opinion",
                                                                                        "Avg Days to Close", "Tenure",
                                                                                        "Close Rate", "Default",
                                                                                        "Pricing", "NPS"])
    processed = obj.preprocess_data(outcome_data, history, company)
    #     available_data_timeline=obj.available_data(processed,obj.snapshot_date)
    #     print available_data_timeline
    #     available_data_timeline.plot(figsize=(15,8))
    model_record = obj.run_health_assessment(processed)
    outcome_timeline = obj.get_outcome_timeline(outcome_data,'Inactivation Date')
    print(outcome_timeline)