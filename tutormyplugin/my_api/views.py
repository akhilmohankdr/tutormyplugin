# tutormyplugin/my_api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User


@api_view(['GET'])
@permission_classes([AllowAny])
def hello_world(request):
    """Simple hello world endpoint - no authentication required"""
    return Response({
        'message': 'Hello from my custom API!',
        'status': 'success',
        'plugin': 'myplugin is working!'
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_api(request):
    """Test endpoint that accepts GET and POST"""
    if request.method == 'POST':
        data = request.data
        return Response({
            'message': 'POST request received',
            'data': data,
            'status': 'success'
        })
    
    return Response({
        'message': 'GET request received',
        'method': request.method,
        'status': 'success'
    })



@api_view(['GET'])
@permission_classes([AllowAny])
def user_list(request):
    users = User.objects.all()[:10]

    data = []
    for u in users:
        data.append({
            "username": u.username,
            "email" : u.email
        })

    return Response({
        "count":len(data),
        "users" :data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def user_stats(request):
    """Get user statistics - TESTING HOOKS!"""
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    return Response({
        "message": "This endpoint was deployed via HOOKS only!",
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "staff_users": staff_users,
            "superusers": superusers,
            "inactive_users": total_users - active_users
        },
        "deployment_method": "PRODUCTION_READY_HOOKS",
        "status": "success"
    })