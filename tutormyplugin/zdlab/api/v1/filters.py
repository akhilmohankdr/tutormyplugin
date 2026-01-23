
import django_filters
#from django.contrib.auth import get_user_model
#from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import (
    CourseOverview,
)


class CourseOverviewFilter(django_filters.FilterSet):

    display_name = django_filters.CharFilter(lookup_expr='icontains')
    org = django_filters.CharFilter(
        name='display_org_with_default', lookup_expr='iexact')
    number = django_filters.CharFilter(
        name='display_number_with_default', lookup_expr='iexact')
    number_contains = django_filters.CharFilter(
        name='display_number_with_default', lookup_expr='icontains')

    class Meta:
        model = CourseOverview
        fields = ['display_name', 'org', 'number', 'number_contains', ]

