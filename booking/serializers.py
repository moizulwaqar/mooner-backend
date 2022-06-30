from rest_framework import serializers
from .models import *
from django.db.models import Avg, Q
from django.utils.translation import gettext_lazy as _
from payments.models import StripeBooking
from datetime import datetime, timezone
from django.utils import timezone


class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        # fields = ['id', 'start_date', 'price', 'category', 'order_status', 'seeker']
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'start_date': {'read_only': True},
            'price': {'read_only': True},
            'category': {'read_only': True},
            'seeker': {'read_only': True}
        }


class BookingAdminSerializer(serializers.ModelSerializer):
    seeker = serializers.CharField(source="ss.username", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'start_date', 'price', 'category', 'order_status', 'seeker']


class BidsSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="job.job_cat_child.name", read_only=True)
    sp_name = serializers.CharField(source="sp.first_name")
    sp_profile_image = serializers.FileField(source="sp.profile.profile_image")
    sp_id = serializers.IntegerField(source="sp.id")

    class Meta:
        model = Bids
        fields = ['id', 'sp_name', 'sp_profile_image', 'sp_id', 'category_name', 'price']

    def validate(self, attr):
        attr["price"] = 1
        return attr

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.job.job_cat_child:
            sp_service = Spservices.objects.filter(s_user=instance.sp_id, s_cat_parent=instance.job.job_cat_child.id)
            if sp_service.exists():
                sp = sp_service.first()
                representation['sp_service_price'] = sp.budget
                representation['service_id'] = sp.id
        sp_ratings = Rating.objects.filter(rated_to=instance.sp_id).aggregate(Avg('star'))
        if sp_ratings:
            representation['sp_rating'] = sp_ratings['star__avg']
        else:
            representation['sp_rating'] = 0
        sp_bookings = Booking.objects.filter(job__sp=instance.sp_id, order_status="Completed").count()
        representation['completed_jobs'] = sp_bookings
        return representation


class SpServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spservices
        fields = '__all__'


class JobsSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="job_cat_child.name", read_only=True)

    def validate(self, attr):
        attr["budget"] = 1
        return attr

    class Meta:
        model = Jobs
        fields = ['id', 'category', 'job_description', 'budget',
                  'job_status', 'job_category', 'job_cat_child', 'ssid', 'sp', 'schedule', 'image_urls'
                  , 'ss_stripe_token', 'ss_stripe_email', 'address', 'floor_no', 'unit_no', 'longitude',
                  'latitude']
        extra_kwargs = {
            'ssid': {'required': True, "allow_null": False},
            'job_category': {'required': True, "allow_null": False},
            'job_cat_child': {'required': True, "allow_null": False},
            'budget': {'required': True, "allow_null": False},
            'job_status': {'required': True, "allow_null": False},
            'job_description': {'required': True, "allow_null": False},
            # 'address': {'required': True, "allow_null": False},
            # 'longitude': {'required': True, "allow_null": False},
            # 'latitude': {'required': True, "allow_null": False},
        }


class RatingSerializer(serializers.ModelSerializer):
    rated_by = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id')
    rated_to = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id')
    booking = serializers.SlugRelatedField(queryset=Booking.objects.all(), slug_field='id')
    feedback = serializers.CharField(required=True)
    star = serializers.FloatField(required=True)

    class Meta:
        model = Rating

        fields = ['id', 'rated_by', 'rated_to', 'booking', 'feedback',
                  'star']


class FilterSPSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="s_cat_parent.name", read_only=True)
    sp_name = serializers.CharField(source="s_user.first_name")
    sp_profile_image = serializers.FileField(source="s_user.profile.profile_image")
    sp_id = serializers.CharField(source="s_user.id")

    class Meta:
        model = Spservices
        fields = ['id', "sp_profile_image", "sp_name", "category_name", "sp_id"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        sp_service = Spservices.objects.filter(s_user=instance.s_user, s_cat_parent=instance.s_cat_parent)
        if sp_service.exists():
            representation['sp_service_price'] = sp_service.first().budget
        sp_ratings = Rating.objects.filter(rated_to=instance.s_user).aggregate(Avg('star'))
        if sp_ratings['star__avg']:
            representation['sp_rating'] = sp_ratings['star__avg']
        else:
            representation['sp_rating'] = 0
        sp_bookings = Booking.objects.filter(job__sp=instance.s_user, order_status="Completed").count()
        representation['completed_jobs'] = sp_bookings
        return representation


class SSBookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(required=True)
    ss_id = serializers.CharField(required=True)

    class Meta:
        model = Booking
        fields = ('booking_id', 'ss_id',)


class SPBookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(required=True)
    sp_id = serializers.CharField(required=True)

    class Meta:
        model = Booking
        fields = ('booking_id', 'sp_id')
        # read_only_fields = ('booking_id', 'token', 'email')


class PaymentAcknowledgeSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(required=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def validate(self, attrs):
        booking_id = attrs.get("booking_id")
        if not Booking.objects.filter(id=booking_id):
            raise serializers.ValidationError({'error': _("Booking does not exists")})
        if not Booking.objects.filter(id=booking_id, order_status='Completed'):
            raise serializers.ValidationError({'error': _("Booking status is not completed")})
        if not StripeBooking.objects.filter(booking_id=booking_id):
            raise serializers.ValidationError({'error': _("Booking does not exists.")})
        return attrs


class AddExtraPriceSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False)
    add_amount = serializers.IntegerField(required=False)
    booking_id = serializers.IntegerField(required=False)
    ss = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)
    sp = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)

    class Meta:
        model = SPAddPrice
        fields = ['id', 'description', 'add_amount', 'booking_id', 'ss', 'sp', 'payment_status']

    def validate(self, attrs):
        description = attrs.get("description")
        add_amount = attrs.get("add_amount")
        booking_id = attrs.get("booking_id")
        user_obj = self.context.get('request').user
        if not booking_id:
            raise serializers.ValidationError({'error': _("Booking Id is required")})
        extra_obj = SPAddPrice.objects.filter(payment_status='Pending', booking_id=booking_id)
        if extra_obj.exists():
            raise serializers.ValidationError({'error': _("You cannot add a new amount if a payment is pending")})
        addprices_count = SPAddPrice.objects.filter(booking_id=booking_id).count()
        if addprices_count == 3:
            raise serializers.ValidationError({'error': _("you can only update the budget only three time")})
        booking = Booking.objects.filter(id=booking_id, sp=user_obj)
        if not booking.exists():
            raise serializers.ValidationError({'error': _("You dont have permission to to add extra budget")})
        if not description:
            raise serializers.ValidationError({'error': _("description and add_amount is required")})
        if not add_amount:
            raise serializers.ValidationError({'error': _("description and add_amount is required")})
        attrs['ss'] = booking.first().ss
        attrs['add_amount'] = 1
        return attrs


class UpdateExtraPriceSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(read_only=True)
    ss = serializers.IntegerField(source="ss.id", read_only=True)
    sp = serializers.IntegerField(source="sp.id", read_only=True)

    class Meta:
        model = SPAddPrice
        fields = ['id', 'description', 'add_amount', 'booking_id', 'ss', 'sp', 'payment_status']


class DisputeSerializer(serializers.ModelSerializer):
    DISPUTE_STATUS = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),

    )
    dispute_status = serializers.ChoiceField(choices=DISPUTE_STATUS, default='Pending')
    booking_id = serializers.IntegerField(required=True)
    reason = serializers.CharField(max_length=400, required=False)
    seeker = serializers.CharField(source="booking.ss.username", read_only=True)
    provider = serializers.CharField(source="booking.sp.username", read_only=True)
    category = serializers.CharField(source="booking.category.name", read_only=True)
    sub_category = serializers.CharField(source="booking.cat_child_id.name", read_only=True)

    class Meta:
        model = Dispute
        fields = ('id', 'dispute_status', 'booking_id', 'ss_created_at', 'admin_updated_at', 'reason', 'seeker',
                  'provider', 'category', 'sub_category')

    def validate(self, attrs):
        if self.context['request'].method == 'POST':
            booking_id = attrs.get('booking_id')
            user_id = self.context.get('request').user.id
            if not Booking.objects.filter(id=booking_id, ss=user_id, order_status='Completed', is_payment=False).exists():
                raise serializers.ValidationError({'error': "Booking does not exits."})
            if Dispute.objects.filter(Q(dispute_status='Pending') | Q(dispute_status='Approved'), booking=booking_id).exists():
                raise serializers.ValidationError({'error': "Dispute already created or approved."})
            if Dispute.objects.filter(booking=booking_id, dispute_status='Rejected').count() == 3:
                raise serializers.ValidationError({'error': "Dispute already Rejected 3 time."})

            return attrs

        else:
            if self.context['request'].method == 'PUT':
                booking_id = attrs.get('booking_id')
                if not Booking.objects.filter(id=booking_id, order_status='Completed', is_payment=True).exists():
                    raise serializers.ValidationError({'error': "Booking does not exits."})
            attrs['admin_updated_at'] = datetime.now(tz=timezone.utc)
            return attrs


class SSActionExtraPriceSerializer(serializers.ModelSerializer):
    action = serializers.CharField(required=False)
    booking_id = serializers.IntegerField(required=False)
    sp_add_price_id = serializers.IntegerField(required=False)

    class Meta:
        model = SPAddPrice
        fields = ['id', 'description', 'add_amount', 'booking_id', 'payment_status', 'sp_add_price_id',
                  'action']

    def validate(self, attrs):
        action = attrs.get("action")
        booking_id = attrs.get("booking_id")
        add_price = attrs.get('sp_add_price_id')
        stripe_token = attrs.get('stripe_token')
        user_obj = self.context.get('request').user

        # if not stripe_token:
        #     raise serializers.ValidationError({'error': _("stripe token is required")})
        if not add_price:
            raise serializers.ValidationError({'error': _("sp_add_price_id is required")})
        if not action:
            raise serializers.ValidationError({'error': _("action is required")})
        if not booking_id:
            raise serializers.ValidationError({'error': _("booking_id is required")})
        ss_price_obj = SPAddPrice.objects.filter(id=add_price, booking_id=booking_id, ss=user_obj)
        if not ss_price_obj.exists():
            raise serializers.ValidationError({'error': _("Object doesn't exists")})
        if action.lower() == 'reject':
            if ss_price_obj.first().payment_status == 'Accept':
                raise serializers.ValidationError({'error': _("You cannot delete this object")})
        booking = Booking.objects.filter(id=booking_id, ss=user_obj)
        if not booking.exists():
            raise serializers.ValidationError({'error': _("You dont have permission to to except and reject the request")})
        attrs['sp'] = booking.first().sp
        attrs["add_amount"] = 1
        return attrs


class TipSerializer(serializers.ModelSerializer):

    status = serializers.BooleanField(default=False)
    booking_id = serializers.IntegerField(required=False)
    ss = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)
    sp = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)
    stripe_token = serializers.CharField(read_only=True)
    charge_id = serializers.CharField(required=False)

    class Meta:
        model = Tip
        fields = ('id', 'status', 'booking_id', 'ss', 'sp', 'amount', 'charge_id', 'stripe_token')

    def validate(self, attrs):
        booking_id = attrs.get('booking_id')
        ss_id = attrs.get('ss')
        sp_id = attrs.get('sp')
        amount = attrs.get('amount')
        if not booking_id:
            raise serializers.ValidationError({'error': "booking id is required."})
        if not ss_id:
            raise serializers.ValidationError({'error': "ss id is required."})
        if not sp_id:
            raise serializers.ValidationError({'error': "sp id is required."})
        if not amount:
            raise serializers.ValidationError({'error': "amount is required."})
        booking_object = Booking.objects.filter(id=booking_id, order_status='Completed', is_payment=True)
        if not booking_object:
            raise serializers.ValidationError({'error': "Booking does not exits."})
        if Tip.objects.filter(booking=booking_id):
            raise serializers.ValidationError({'error': "Tip already awarded."})
        if not booking_object.first().ss == ss_id:
            raise serializers.ValidationError({'error': "ss_id is not valid."})
        if not booking_object.first().sp == sp_id:
            raise serializers.ValidationError({'error': "sp_id is not valid."})
        return attrs


class AdminConvenienceFeeSerializer(serializers.ModelSerializer):
    admin_fees = serializers.IntegerField(required=True)
    convenience_fees = serializers.IntegerField(required=True)

    class Meta:
        model = AdminConvenienceFee
        fields = ('id', 'admin_fees', 'convenience_fees')


class AdminTransactionListSerializer(serializers.ModelSerializer):
    admin = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id')
    admin_name = serializers.CharField(source='admin.username', read_only=True)
    booking = serializers.SlugRelatedField(queryset=Booking.objects.all(), slug_field='id')
    earn_tokens = serializers.CharField(max_length=255)
    ss_id = serializers.IntegerField(source='booking.ss.id', read_only=True)
    ss_name = serializers.CharField(source='booking.ss.first_name', read_only=True)
    sp_id = serializers.IntegerField(source='booking.sp.id', read_only=True)
    sp_name = serializers.CharField(source='booking.sp.first_name', read_only=True)
    job_id = serializers.IntegerField(source='booking.job.id', read_only=True)
    job_description = serializers.CharField(source='booking.job.job_description', read_only=True)

    class Meta:
        model = AdminTransactionList
        fields = ('id', 'admin', 'admin_name', 'booking', 'earn_tokens', 'ss_name', 'sp_name', 'job_id',
                  'job_description', 'ss_id', 'sp_id')


class BookingDateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = ['id', 'start_date', 'end_date']
        extra_kwargs = {
            'id': {'read_only': True},
            'start_date': {'required': True},
            'end_date': {'required': True},
        }

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date < timezone.now():
            raise serializers.ValidationError({'error': "please enter current date/time or any upcoming date."})
        if end_date < timezone.now():
            raise serializers.ValidationError({'error': "please enter current date/time or any upcoming date/time which"
                                                        "is greater than start date."})
        if start_date > end_date:
            raise serializers.ValidationError({'error': "start date/time should be less than end date/time."})

        return attrs
