from rest_framework import viewsets, exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import *
# Create your views here.


class PrivacyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PrivacyPolicySerializer
    queryset = PrivacyPolicy.objects.all()

    def create(self, request, *args, **kwargs):
        if request.user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            serializer.save(user=request.user)

            return Response({"status": True, "message": "Privacy has been created successfully.", "data": serializer.data})
        raise exceptions.PermissionDenied()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"status": True, "message": "Privacy content", "data": serializer.data})

    def update(self, request, *args, **kwargs):
        if request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response({"status": True, "message": "Privacy has been updated successfully.", "data": serializer.data})
        raise exceptions.PermissionDenied()

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"status": True, "message": "Privacy successfully deleted!"})
        raise exceptions.PermissionDenied()

    def perform_destroy(self, instance):
        instance.delete()


class AboutContentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AboutContentSerializer
    queryset = AboutContent.objects.all()

    def create(self, request, *args, **kwargs):
        if request.user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            serializer.save(user=request.user)

            return Response({"status": True, "message": "About Content has been created successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"status": True, "message": "About Content", "data": serializer.data})

    def update(self, request, *args, **kwargs):
        if request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response({"status": True, "message": "About Content has been updated successfully.", "data": serializer.data})
        raise exceptions.PermissionDenied()

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"status": True, "message": "About Content successfully deleted!"})
        raise exceptions.PermissionDenied()

    def perform_destroy(self, instance):
        instance.delete()


class TermsAndConditionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TermsAndConditionSerializer
    queryset = TermsAndCondition.objects.all()

    def create(self, request, *args, **kwargs):
        if request.user.is_superuser:
            serializer = self.get_serializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            serializer.save(user=request.user)

            return Response({"status": True, "message": "Terms and condition has been created successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"status": True, "message": "Terms and condition", "data": serializer.data})

    def update(self, request, *args, **kwargs):
        if request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response({"status": True, "message": "Terms and condition has been updated successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"status": True, "message": "Terms and condition successfully deleted!"})
        raise exceptions.PermissionDenied()

    def perform_destroy(self, instance):
        instance.delete()