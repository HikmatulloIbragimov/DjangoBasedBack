from django.db import models

class Transaction(models.Model):
    user = models.ForeignKey('app.TelegramUser', on_delete=models.CASCADE)
    merchandise = models.ForeignKey('app.Merchandise', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    inputs = models.JSONField()

    amount = models.PositiveBigIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    server_response = models.TextField(blank=True)
    is_accepted = models.BooleanField(default=False)
    status = models.CharField(max_length=100, blank=True, default="ontheway") # status are ontheway, delivered, failed

    def __str__(self):
        return f"{self.user.username} - {self.amount}"