from django.db import models

class TelegramUser(models.Model):
    user_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    photo_url = models.URLField(null=True, blank=True)
    

    balance = models.IntegerField(default=0)

    def __str__(self):
        return self.username or self.user_id
    

class Card(models.Model):
    number = models.CharField(max_length=16)
    cardholder_name = models.CharField(max_length=100)

    def __str__(self):
        return self.cardholder_name
    
class Game(models.Model):
    name = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)

    slug = models.SlugField()
    image_path = models.URLField()

    servers = models.ManyToManyField('Server', blank=True)
    categories = models.ManyToManyField('Category')
    inputs = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name
    
class Server(models.Model):
    name = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)

    slug = models.SlugField()

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)

    description = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    description_en = models.TextField(blank=True)

    slug = models.SlugField()

    def __str__(self):
        return self.name
    
class Merchandise(models.Model):
    name = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)

    price = models.CharField(max_length=100)
    currency = models.CharField(max_length=100)
    currency_ru = models.CharField(max_length=100)
    currency_en = models.CharField(max_length=100)
    
    # relations using slug as charfield
    game = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    server = models.CharField(max_length=100, null=True, blank=True)

    tags = models.CharField(max_length=100, null=True, blank=True)

    enabled = models.BooleanField(default=True)

    reseller_id = models.CharField(max_length=100)
    reseller_category = models.CharField(max_length=100)

    slug = models.SlugField()

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.server:
            self.server = ''
        super().save(*args, **kwargs)