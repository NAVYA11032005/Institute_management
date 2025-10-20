from django.db import models
from apps.Teams.models import Team

class Expense(models.Model):
    expense_name = models.CharField(max_length=255)
    expense_by = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.expense_name} - ₹{self.amount} by {self.expense_by.name}"
