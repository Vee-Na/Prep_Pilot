from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):

    def has_permission(self, request, view):

        return bool(request.user and request.user.is_authenticated and request.user.role=='Admin') 

class IsInterviewee(BasePermission):

    def has_permission(self, request, view):

        return bool(request.user and request.user.is_authenticated and request.user.role=='Interviewee') 