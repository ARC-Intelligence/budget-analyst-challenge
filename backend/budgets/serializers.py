from rest_framework import serializers

from .models import LineItem, Scenario


class ScenarioSerializer(serializers.ModelSerializer):
    line_item_count = serializers.SerializerMethodField()

    class Meta:
        model = Scenario
        fields = ["id", "name", "description", "created_at", "line_item_count"]

    def get_line_item_count(self, obj):
        return obj.line_items.count()


class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = "__all__"
