from django.db import models


class Scenario(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LineItem(models.Model):
    scenario = models.ForeignKey(
        Scenario, related_name="line_items", on_delete=models.CASCADE
    )
    department = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    month = models.DateField()
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2)
    actual_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["department", "category", "month"]

    def __str__(self):
        return f"{self.department} / {self.category} / {self.month:%Y-%m}"
