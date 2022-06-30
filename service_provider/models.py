from django.db import models
from django.contrib.auth.models import User
from category_management.models import Category, CategoryQuestions

# Create your models here.


METHOD = (
    ('Take away', 'Take away'),
    ('Dine', 'Dine'),
    ('Delivery', 'Delivery')
)


class SpItems(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="category", null=True,
                                      blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user", null=True,
                             blank=True)
    name = models.CharField(max_length=250, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    method = models.CharField(max_length=50, choices=METHOD, null=True, blank=True, default='Take away')
    description = models.CharField(max_length=250, null=True, blank=True)
    opening = models.TimeField(null=True, blank=True)
    closing = models.TimeField(null=True, blank=True)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


class SpItemImages(models.Model):
    item = models.ForeignKey(SpItems, on_delete=models.CASCADE, related_name="item_images")
    image = models.FileField(upload_to="sp_item_image/")
