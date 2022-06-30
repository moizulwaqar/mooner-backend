from django.db import models
from treenode.models import TreeNodeModel
from django.contrib.auth.models import User
from django_softdelete.models import SoftDeleteModel
import datetime

USER_TYPE = (
    ('SS', 'SS'),
    ('SP', 'SP'),
)


class Referral(SoftDeleteModel, TreeNodeModel):

    # the field used to display the model instance
    # default value 'pk'
    treenode_display_field = 'user'

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_in_referral')


    class Meta(TreeNodeModel.Meta):
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'


class LevelsPercentage(models.Model):

    level_0 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    level_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    level_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    level_3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    level_4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.today)
    updated_at = models.DateTimeField(auto_now_add=True)


class TokenHistory(models.Model):

    earned_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='earned_by_user')
    earned_from = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='earned_from_user')
    earn_tokens = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.today)
    updated_at = models.DateTimeField(auto_now_add=True)
    earned_user_type = models.CharField(max_length=50, choices=USER_TYPE, null=True, blank=True)