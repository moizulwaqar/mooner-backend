from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    # path('add_category/', AddCategory.as_view()),
    # path('add_category/<int:pk>',UpdateCategory.as_view()),
    path('categories/', Categories.as_view()),
    path('categories/<int:pk>', UpdateCategories.as_view()),
    path('questions/', AddListQuestion.as_view()),
    path('updateQuestions/<int:pk>', UpdateQuestions.as_view()),
    path('get_childs/', get_childs.as_view(), name='get_childs'),
    path('searchcategory/',SearchCategoryView.as_view(), name='searchcategory'),
    path('get_questions/', GetQuestions.as_view(), name='get_questions'),
    path('soft_del_category/', SoftDeleteCategory.as_view(), name='soft_del_category'),
    path('hard_del_category/', HardDeleteCategory.as_view(), name='hard_del_category'),
    path('restore_category/', RestoreCategory.as_view(), name='restore_category'),
    path('soft_del_record/', SoftDeleteRecord.as_view(), name='soft_del_record'),
    path('active_category/', ActiveCategory.as_view(), name='active_category'),

    # category and question search
    path('search_categories/', SearchCategory.as_view()),
    path('search_questions/', SearchQuestions.as_view()),

    # hard delete categories of soft_deleted category
    path('category_list_del/', CategoryListDel.as_view(), name='category_list_del'),

    # path('categories/', categories , name='categories')

    # parent and sub_category registered users
    path('category_registered_users/<int:pk>/', CategoryRegisteredUsers.as_view()),

]

