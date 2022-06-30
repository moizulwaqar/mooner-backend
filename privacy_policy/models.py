from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class PrivacyPolicy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_privacy_policy", null=True,
                             blank=True,
                             verbose_name="Privacy Policy User")
    policy_content = models.TextField()

    def __str__(self):
        return self.policy_content

    class Meta:
        ordering = ['-id']


class AboutContent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_about_content", null=True,
                             blank=True,
                             verbose_name="About Content User")
    about_content = models.TextField()

    def __str__(self):
        return self.about_content

    class Meta:
        ordering = ['-id']


class TermsAndCondition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_term_condition", null=True,
                             blank=True,
                             verbose_name="Terms and condition user")
    terms_and_condition = models.TextField()

    def __str__(self):
        return self.terms_and_condition

    class Meta:
        ordering = ['-id']