from django.db import models

class Setting(models.Model):
    admission_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Admission Fee (₹)",
        help_text="This fee will automatically be added to every new student's payment",
        default=0  # <--- Add a default to prevent IntegrityError
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings (Admission Fee: ₹{self.admission_fee})"

    class Meta:
        verbose_name = "Setting"
        verbose_name_plural = "Settings"
