from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework import serializers

from health_assessment.models import Run

import uuid

def upload_file_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.run_id, filename)


class UserSerializer(serializers.ModelSerializer):
    run = serializers.PrimaryKeyRelatedField(many=True, queryset=Run.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'run']
        write_only_fields = ('password',)
        
    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class RunSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField(source='user_id.id')
    run_id = serializers.ReadOnlyField()
    gainsight = serializers.BooleanField()
    outcome_data = serializers.FileField()
    scorecard_history = serializers.FileField()
    account_details = serializers.FileField() 
    preprocessed_file = serializers.ReadOnlyField()
    id_field = serializers.CharField()
    churn_date = serializers.CharField()
    snapshot_date = serializers.CharField()

    class Meta:
        model = Run
        fields = [
                    'id', 
                    'user_id', 
                    'run_id', 
                    'gainsight', 
                    'outcome_data', 
                    'scorecard_history', 
                    'account_details', 
                    'preprocessed_file', 
                    'id_field', 
                    'churn_date', 
                    'snapshot_date'
                ]

    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        return Run.objects.create(**validated_data)
