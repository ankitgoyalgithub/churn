import datetime
import json
import logging
import pandas as pd
import sys
import traceback
import uuid

from django.conf import settings
from django.views import generic

from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status

from health_assessment.models import Run
from health_assessment.Lib.healthassessment import HealthAssessment
from health_assessment.utils import get_insights


logger = logging.getLogger(__name__)

class Availability(generic.ListView):
    template_name = "index.html"
    context_object_name = "data"

    def get_queryset(self):
        data = dict()
        return data

class AvailabilityChart(generic.ListView):
    template_name = "availability.html"
    context_object_name = "data"

    def get_queryset(self):
        data = dict()
        return data

"""
API to Upload Files
"""
#TO DO
# Pre processing (Joining for Gainsight Data) 
# Gainsight/ Non Gainsight
@api_view(['POST'])
def file(request):
    try:
        post_data = request.POST
        print(post_data)
        gainsight = post_data.get('gainsight', None)
        id_field = post_data.get('id_field', None)
        churn_date = post_data.get('churn_date', None)
        snapshot_date = post_data.get('snapshot_date', None)

        if (gainsight is None) or (id_field is None) or (churn_date is None) or (snapshot_date is None):
            raise APIException(detail="One of Mandatory Fields(gainsight, id_field, churn_date, snapshot_date) is Missing ", code=status.HTTP_400_BAD_REQUEST)

        if not request.FILES:
            raise APIException(detail="No Files Uploaded", status=status.HTTP_400_BAD_REQUEST)
        else:
            directory_name = uuid.uuid4()
            gainsight = 1 if gainsight == 'on' else 0
            run = Run()
            run.scorecard_history=request.FILES['scorecard_history']
            run.outcome_data=request.FILES['outcome_data']

            if gainsight == 1:
                run.account_details=request.FILES['account_details']
            
            run.snapshot_date = snapshot_date
            run.churn_date = churn_date
            run.id_field = id_field
            run.gainsight = gainsight
            run.run_id = directory_name
            run.save()
            logger.info(f"Run Created Successfully with RunId {directory_name}")
        return Response({
            "run_id": str(directory_name),
            "details": "Success",
            "status": status.HTTP_200_OK})
    except Exception as e:
        exec_info = sys.exc_info()
        traceback.print_exception(*exec_info)
        raise APIException("Unable to Save Details")

@api_view(['GET'])
def data_availability(request, run_id):
    try:
        response = dict()
        run = Run.objects.get(run_id=run_id)
        use_case = "Gainsight" if run.gainsight else ""
        outcome_data = pd.read_csv(run.outcome_data.path, encoding="cp1252")
        history_data = pd.read_csv(run.scorecard_history.path, encoding="cp1252")
        company_data = None

        if run.gainsight:
            company_data = pd.read_csv(run.account_details.path, encoding="cp1252")
        
        obj=HealthAssessment(ID = run.id_field, churn_date = 'Inactivation Date', snapshot_date = 'Snapshot Date',target = 'Status', metrics_col=["Create Offer Tool",
                        "Lost Sales","Last Visit","Opinion Scores","GM Tenure","Billing","CSM Opinion","CSS Opinion",
                        "Avg Days to Close","Tenure","Close Rate","Default","Pricing","NPS"])
        processed=obj.preprocess_data(outcome_data, history_data, company_data)
        model_record=obj.run_health_assessment(processed)
        available_data_timeline=obj.available_data(processed,obj.snapshot_date)
        
        for index, row in available_data_timeline.iterrows():
            if index[0] not in response:
                response[index[0]] = {}
                response[index[0]][index[1]] = {}
            elif index[1] not in response[index[0]]:
                response[index[0]][index[1]] = {}

            response[index[0]][index[1]]['Create Offer Tool'] = row['Create Offer Tool']
            response[index[0]][index[1]]['Lost Sales'] = row['Lost Sales']
            response[index[0]][index[1]]['Last Visit'] = row['Last Visit']
            response[index[0]][index[1]]['Opinion Scores'] = row['Opinion Scores']
            response[index[0]][index[1]]['GM Tenure'] = row['GM Tenure']
            response[index[0]][index[1]]['Billing'] = row['Billing']
            response[index[0]][index[1]]['CSM Opinion'] = row['CSM Opinion']
            response[index[0]][index[1]]['CSS Opinion'] = row['CSS Opinion']
            response[index[0]][index[1]]['Avg Days to Close'] = row['Avg Days to Close']
            response[index[0]][index[1]]['Tenure'] = row['Tenure']
            response[index[0]][index[1]]['Close Rate'] = row['Close Rate']
            response[index[0]][index[1]]['Default'] = row['Default']
            response[index[0]][index[1]]['Pricing'] = row['Pricing']
            response[index[0]][index[1]]['NPS'] = row['NPS']
            response[index[0]][index[1]]['Account ID'] = row['Account ID']
            response[index[0]][index[1]]['Snapshot Date'] = row['Snapshot Date']
            response[index[0]][index[1]]['Inactivation Date'] = row['Inactivation Date']
            response[index[0]][index[1]]['Status'] = row['Status']
            response[index[0]][index[1]]['week'] = row['week']
        return Response(response)
    except Exception as e:
        logger.error(str(e))
        exec_info = sys.exc_info()
        traceback.print_exception(*exec_info)
        raise APIException(str(e))

@api_view(['POST'])
def metrics_assessment(request, run_id):
    try:
        cols=['Create Offer Tool', 'Lost Sales', 'Last Visit', 'GM Tenure', 'Billing', 'CSM Opinion', 'CSS Opinion',
            'Avg Days to Close', 'Tenure', 'Close Rate', 'Pricing', 'NPS']

        run = Run.objects.get(run_id=run_id)
        use_case = "Gainsight" if run.gainsight else ""
        outcome_data = pd.read_csv(run.outcome_data.path, encoding="cp1252")
        history_data = pd.read_csv(run.scorecard_history.path, encoding="cp1252")
        company_data = None

        if run.gainsight:
            company_data = pd.read_csv(run.account_details.path, encoding="cp1252")
        
        obj=HealthAssessment(ID ='Account ID', churn_date = 'Inactivation Date', snapshot_date = 'Snapshot Date',target = 'Status', metrics_col=["Create Offer Tool",
                        "Lost Sales","Last Visit","Opinion Scores","GM Tenure","Billing","CSM Opinion","CSS Opinion",
                        "Avg Days to Close","Tenure","Close Rate","Default","Pricing","NPS"])
        processed=obj.preprocess_data(outcome_data, history_data, company_data)
        model_record=obj.run_health_assessment(processed)
        model_record.fillna(0, inplace=True)
        model_record.model_status=model_record.model_status.apply(lambda x: 0 if x=='Active' else 1) 
        ks_output_dict = get_insights(model_record, cols, 'model_status', [3,4,5])
        return Response({
            "run_id": run_id
        })
    except Exception as e:
        logger.error(str(e))
        exec_info = sys.exc_info()
        traceback.print_exception(*exec_info)
        raise APIException(str(e))