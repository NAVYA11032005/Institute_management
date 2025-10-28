from django.db import models
from django.utils import timezone
from apps.Teams.models import Team

class Expense(models.Model):
    expense_name = models.CharField(max_length=255)
    expense_by = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    
    # Add these two fields for soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def __str__(self):
        return f"{self.expense_name} - ₹{self.amount} by {self.expense_by.name}"
