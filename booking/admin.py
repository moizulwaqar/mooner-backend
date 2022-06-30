from django.contrib import admin
from .models import *
from mooner_backend.utils import admin_softdelete_record
# Register your models here.

class JobsAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        all_records = admin_softdelete_record(self, request)
        return all_records


admin.site.register(Jobs, JobsAdmin)


class AnswerAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        all_records = admin_softdelete_record(self, request)
        return all_records


admin.site.register(Answer,AnswerAdmin)


class BookingAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        all_records = admin_softdelete_record(self, request)
        return all_records


admin.site.register(Booking, BookingAdmin)
admin.site.register(SPAddPrice)
admin.site.register(Spservices)
admin.site.register(Bids)
admin.site.register(Rating)
admin.site.register(JobFiles)
admin.site.register(SpServiceImages)
admin.site.register(Dispute)
admin.site.register(Tip)
admin.site.register(AdminConvenienceFee)
admin.site.register(AdminTransactionList)
