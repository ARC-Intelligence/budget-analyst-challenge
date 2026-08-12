from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import LineItem, Scenario
from .serializers import LineItemSerializer, ScenarioSerializer


class LineItemPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    pagination_class = None


class LineItemViewSet(viewsets.ModelViewSet):
    queryset = LineItem.objects.all()
    serializer_class = LineItemSerializer
    pagination_class = LineItemPagination

    def get_queryset(self):
        qs = super().get_queryset()
        scenario = self.request.query_params.get("scenario")
        if scenario:
            qs = qs.filter(scenario_id=scenario)
        department = self.request.query_params.get("department")
        if department:
            qs = qs.filter(department=department)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs
