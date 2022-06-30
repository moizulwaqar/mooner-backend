from django.db import models
from django.contrib.auth.models import User
from django.db import models
from treenode.models import TreeNodeModel
from django_softdelete.models import SoftDeleteModel
# Create your models here.


class Category(TreeNodeModel, SoftDeleteModel):

    # the field used to display the model instance
    # default value 'pk'

    treenode_display_field = 'name'
    name = models.CharField(max_length=50)
    cat_icon = models.FileField(upload_to='category_icon/', null=True, blank=True)
    category_image = models.FileField(upload_to='category_image/', null=True, blank=True)
    category_heading_text = models.CharField(max_length=250, null=True, blank=True)
    sp = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='sp_category')
    is_registered = models.BooleanField(default=False)
    category_heading_text2 = models.CharField(max_length=250, null=True, blank=True)
    behaviour = models.CharField(max_length=250, default="Default")


class Meta(TreeNodeModel.Meta):
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class CategoryQuestions(SoftDeleteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                             related_name='categoryquestions_user')
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='doc_sub_category')
    sub_category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='category_questions')
    sub_category_child = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                           related_name='sub_category_child_in_category_questions')
    question_text = models.CharField(max_length=250, default="", null=True, blank=True)
    question_type = models.CharField(max_length=250, default="", null=True, blank=True)
    question_for = models.CharField(max_length=250, default="", null=True, blank=True)
    r_question_text = models.CharField(max_length=250, default="", null=True, blank=True)
    r_text_one = models.CharField(max_length=250, default="", null=True, blank=True)
    r_text_two = models.CharField(max_length=250, default="", null=True, blank=True)
    r_text_three = models.CharField(max_length=250, default="", null=True, blank=True)
    r_text_four = models.CharField(max_length=250, default="", null=True, blank=True)
    r_text_five = models.CharField(max_length=250, default="", null=True, blank=True)
    r_text_six = models.CharField(max_length=250, default="", null=True, blank=True)
    # class Meta:
    #     permissions = [
    #         ("View_list_of_CategoryQuestions", "Can view List of CategoryQuestions"),
    #     ]



