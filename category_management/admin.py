from django.contrib import admin
from .models import *
from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm
# Register your models here
# admin.site.register(Categories)
# admin.site.register(SubCategory)
from mooner_backend.utils import admin_softdelete_record


class CategoryQuestionsAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        all_records = admin_softdelete_record(self, request)
        return all_records


admin.site.register(CategoryQuestions,CategoryQuestionsAdmin)


class CategoryAdmin(TreeNodeModelAdmin):

    # set the changelist display mode: 'accordion', 'breadcrumbs' or 'indentation' (default)
    # when changelist results are filtered by a querystring,
    # 'breadcrumbs' mode will be used (to preserve data display integrity)
    treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_BREADCRUMBS
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_INDENTATION

    # use TreeNodeForm to automatically exclude invalid parent choices
    form = TreeNodeForm

    def get_queryset(self, request):
        all_records = admin_softdelete_record(self, request)
        return all_records


admin.site.register(Category, CategoryAdmin)