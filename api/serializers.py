from rest_framework import serializers
from detector.models import *


class GmailAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = GmailAccount
        fields = '__all__'


class EmailMessagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailMessage
        fields = '__all__'


class LinkAnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = LinkAnalysis
        fields = '__all__'


class AIDetectionResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = AIDetectionResult
        fields = '__all__'


class ScanHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ScanHistory
        fields = '__all__'


class ThreatStatisticsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThreatStatistics
        fields = '__all__'

