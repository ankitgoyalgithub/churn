import datetime
import json
import logging
import math
import os
import pandas as pd
import sys
import traceback
import uuid

from django.conf import settings
from django.views import generic
from django.http import FileResponse, HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from health_assessment.models import Run, Report
from health_assessment.Lib.healthassessment import HealthAssessment
from health_assessment.utils import get_insights, read_s3_file
from health_assessment.serializers import RunSerializer, UserSerializer


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


class MetricsAssessment(generic.ListView):
    template_name = "assessment.html"
    context_object_name = "data"

    def get_queryset(self):
        data = dict()
        return data


class SourceConnector(generic.ListView):
    template_name = "s3connector.html"
    context_object_name = "data"

    def get_queryset(self):
        data = dict()
        return data


def report_manager(request, *args, **kwargs):
    try:
        report_types = {"reports": []}
        run_id = kwargs["run_id"]
        run = Run.objects.get(run_id=run_id)
        reports = Report.objects.filter(run_id=run.id)
        for r in reports:
            report_types["reports"].append({"name": r.report_name, "id": r.id})
        return render(request, "report_manager.html", report_types)
    except Exception as e:
        logger.error("Error Occured While Rendering Reports Manager")
        logger.error(str(e))
        raise e


"""
API to Upload Files
"""
# TO DO
# Pre processing (Joining for Gainsight Data)
# Gainsight/ Non Gainsight
@api_view(["POST"])
def file(request):
    try:
        post_data = request.POST
        gainsight = post_data.get("gainsight", None)
        id_field = post_data.get("id_field", None)
        churn_date = post_data.get("churn_date", None)
        snapshot_date = post_data.get("snapshot_date", None)
        metric_cols = post_data.get("metric_fields", None)

        if (
            (gainsight is None)
            or (id_field is None)
            or (churn_date is None)
            or (snapshot_date is None)
        ):
            raise APIException(
                detail="One of Mandatory Fields(gainsight, id_field, churn_date, snapshot_date) is Missing ",
                code=status.HTTP_400_BAD_REQUEST,
            )

        if not request.FILES:
            raise APIException(
                detail="No Files Uploaded", status=status.HTTP_400_BAD_REQUEST
            )
        else:
            directory_name = uuid.uuid4()
            gainsight = 1 if gainsight == "on" else 0
            run = Run()
            run.scorecard_history = request.FILES["scorecard_history"]
            run.outcome_data = request.FILES["outcome_data"]

            if gainsight == 1:
                run.account_details = request.FILES["account_details"]

            run.snapshot_date = snapshot_date
            run.churn_date = churn_date
            run.id_field = id_field
            run.gainsight = gainsight
            run.run_id = directory_name
            run.metric_cols = metric_cols
            run.save()
            run_id_str = directory_name.urn[9:]
            logger.info("Run Created Successfully with RunId " + run_id_str)
        return Response(
            {"run_id": run_id_str, "details": "Success", "status": status.HTTP_200_OK}
        )
    except Exception as e:
        exec_info = sys.exc_info()
        traceback.print_exception(*exec_info)
        raise APIException("Unable to Save Details")


@api_view(["GET"])
def data_availability(request, run_id):
    try:
        response = dict()
        run = Run.objects.get(run_id=run_id)
        use_case = "Gainsight" if run.gainsight else ""
        outcome_data = pd.read_csv(run.outcome_data.path, encoding="cp1252")
        history_data = pd.read_csv(run.scorecard_history.path, encoding="cp1252")
        company_data = None
        metric_cols = run.metric_cols.split(",")

        if run.gainsight:
            company_data = pd.read_csv(run.account_details.path, encoding="cp1252")

        obj = HealthAssessment(
            ID=run.id_field,
            churn_date=run.churn_date,
            snapshot_date=run.snapshot_date,
            target="Status",
            metrics_col=metric_cols,
        )

        processed = obj.preprocess_data(outcome_data, history_data, company_data)
        obj.run_health_assessment(processed)
        available_data_timeline = obj.available_data(processed, obj.snapshot_date)

        for index, row in available_data_timeline.iterrows():
            if index[0] not in response:
                response[index[0]] = {}
                response[index[0]][index[1]] = {}
            elif index[1] not in response[index[0]]:
                response[index[0]][index[1]] = {}

            for col in metric_cols:
                response[index[0]][index[1]][col] = row[col]
        return Response(response)
    except Exception as e:
        logger.error(str(e))
        exec_info = sys.exc_info()
        traceback.print_exception(*exec_info)
        raise APIException(str(e))


@api_view(["GET"])
def download(request, report_id):
    report = Report.objects.get(id=report_id)
    file_path = settings.DOMAIN + "/media" + report.report_path.split("media")[1]
    response = {"path": file_path}
    return Response(response)


@api_view(["GET"])
def metrics_assessment(request, run_id):
    try:
        report_path = os.path.join(settings.MEDIA_ROOT, "user_" + run_id)

        run = Run.objects.get(run_id=run_id)
        use_case = "Gainsight" if run.gainsight else ""
        outcome_data = pd.read_csv(run.outcome_data.path, encoding="cp1252")
        history_data = pd.read_csv(run.scorecard_history.path, encoding="cp1252")
        company_data = None
        cols = run.metric_cols.split(",")

        if run.gainsight:
            company_data = pd.read_csv(run.account_details.path, encoding="cp1252")

        obj = HealthAssessment(
            ID="Account ID",
            churn_date=run.churn_date,
            snapshot_date=run.snapshot_date,
            target="Status",
            metrics_col=cols,
        )

        processed = obj.preprocess_data(outcome_data, history_data, company_data)
        model_record = obj.run_health_assessment(processed)
        model_record.fillna(0, inplace=True)
        model_record.model_status = model_record.model_status.apply(
            lambda x: 0 if x == "Active" else 1
        )
        ks_output_dict = get_insights(
            data=model_record, metrics_cols=cols, target_col="model_status"
        )

        output_ks_dict = dict()

        for key in ks_output_dict:
            output_ks_dict[key] = []
            for index in ks_output_dict[key]["kstable"].index:
                current_risk_value = ks_output_dict[key]["kstable"][
                    "Intensity of Risk"
                ][index]
                if math.isnan(current_risk_value):
                    output_ks_dict[key].append(
                        {"bin": str(index), "value": 0,}
                    )
                else:
                    output_ks_dict[key].append(
                        {"bin": str(index), "value": current_risk_value,}
                    )

        create_report_entry = True
        outcome_timeline_reportpath = os.path.join(report_path, "outcome_timeline.csv")

        if os.path.exists(outcome_timeline_reportpath):
            create_report_entry = False

        outcome_timeline = obj.get_outcome_timeline(
            outcome_data, "Inactivation Date"
        )  # OutCome Timeline Report
        outcome_timeline.to_csv(outcome_timeline_reportpath, header=True)

        if create_report_entry:
            report = Report(
                run_id=run,
                report_name="Monthly Target Distribution",
                report_path=outcome_timeline_reportpath,
            )
            report.save()

        return Response({"run_id": run_id, "ks_dict": output_ks_dict})
    except Exception as e:
        logger.exception(e)
        raise APIException(str(e))


@api_view(["POST"])
def s3_file(request):
    try:
        secret_id = request.POST.get("secretId", None)
        secret_key = request.POST.get("secretKey", None)
        bucket_name = request.POST.get("bucketName", None)
        file_path = request.POST.get("filePath", None)

        header, data = read_s3_file(
            bucket_name=bucket_name,
            file_path=file_path,
            aws_access_key_id=secret_id,
            aws_secret_access_key=secret_key,
        )

        return Response({"headers": header, "data": data})
    except Exception as e:
        raise APIException(str(e))


class RunList(generics.ListCreateAPIView):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        run_id = str(uuid.uuid4())
        token = request.META.get("HTTP_AUTHORIZATION", None).split(" ")[1]
        user_id = Token.objects.get(key=token).user_id
        user = User.objects.get(id=user_id)
        self.serializer_class = RunSerializer(data=request.data)

        if self.serializer_class.is_valid():
            self.serializer_class.save(run_id=run_id, preprocessed_file="test.txt")
            return Response(self.serializer_class.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                self.serializer_class.errors, status=status.HTTP_400_BAD_REQUEST
            )


class RunDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
