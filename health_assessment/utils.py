import boto3

from health_assessment.Lib.AutoBinning import AutoBinning
from health_assessment.Lib.KS import KS


def get_insights(data=None, metrics_cols=None, target_col=None, bins_to_try=[3, 4, 5]):
    best_bin_result_dict = {}

    for each in metrics_cols:
        obj = AutoBinning(target_col, each, [3, 4, 5])
        result_bin, result_threshold = obj.fit(data)
        best_bin_result_dict[each] = result_threshold

    ks_output_dict = {}
    for each in best_bin_result_dict.keys():
        ksdev, kstable = KS(
            data.model_status, data[each], bincuts=best_bin_result_dict[each]
        )  # bincuts
        kstable["Intensity of Risk"] = (
            kstable["dvrate"] * 1.0 / kstable.cumdvrate.values[-1]
        )
        ks_output_dict[each] = {
            "ksvalue": ksdev,
            "kstable": kstable[["Intensity of Risk"]],
        }
    return ks_output_dict


def read_s3_file(
    bucket_name=None, file_path=None, aws_access_key_id=None, aws_secret_access_key=None
):
    """
    Reads a File from AWS S3
    """
    try:
        if aws_access_key_id is None:
            raise Exception("Missing Access Key Id")

        if aws_secret_access_key is None:
            raise Exception("Missing Secret Access Key")

        if bucket_name is None:
            raise Exception("Missing Bucket Key")

        if file_path is None:
            raise Exception("Missing File Path")

        headers = list()
        data = list()

        s3_connection = boto3.resource(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        bucket_connection = s3_connection.Bucket(bucket_name)

        for obj in bucket_connection.objects.filter(Prefix=file_path):
            for line in obj.get()["Body"].read().splitlines():
                if len(headers) == 0:
                    headers = line.decode().split(",")
                else:
                    data.append(line.decode().split(","))

        return headers, data
    except Exception as e:
        raise e

