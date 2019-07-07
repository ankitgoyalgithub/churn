import datetime
import json
import logging
import sys
import traceback
import uuid

from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status

from health_assessment.models import Run

logger = logging.getLogger(__name__)

"""
API to Upload Files
"""
#TO DO
# Pre processing (Joining for Gainsight Data) 
# Gainsight/ Non Gainsight
@api_view(['POST'])
def file(request):
    try:
        media_url = settings.MEDIA_ROOT
        post_data = request.POST
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
            gainsight = 1 if gainsight == 'true' else 0
            id_field = id_field[0]
            churn_date = churn_date
            snapshot_date = snapshot_date
            run = Run()
            run.scorecard_history=request.FILES['scorecard_history']
            run.outcome_data=request.FILES['outcome_data']
            run.account_details=request.FILES['account_details']
            run.preprocessed_file=request.FILES['preprocessed_file']
            run.snapshot_date=datetime.datetime.strptime(snapshot_date, '%d/%m/%Y')
            run.churn_date=datetime.datetime.strptime(churn_date, '%d/%m/%Y')
            run.id_field=id_field
            run.gainsight=gainsight
            run.run_id=directory_name
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

@api_view(['POST'])
def data_availability(request, run_id):
    try:
        run = Run.objects.get(run_id=run_id)
    except Exception as e:
        logger.error(str(e))
        exec_info = sys.exc_info()
        traceback.print_exception(*exec_info)
        raise APIException("Error While Generating Availability Data")

@api_view(['POST'])
def metrics_assessment(request, run_id):
    try:
        pass
        # return table, Field Separation
    except Exception as e:
        logger.error(str(e))
        exec_info = sys.exc_info()
        traceback.print_exception(*exec_info)
        raise APIException("Error While Generating Availability Data")