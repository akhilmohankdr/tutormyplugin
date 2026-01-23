"""URL definitions for Zdlab API version 1
"""

from django.urls import include, re_path
from rest_framework import routers

# Initially doing relative pathing because the full path is a mouthful and a half:
#  `openedx.core.djangoapps.appsembler.api`

from tutormyplugin.zdlab.api.v1 import views


router = routers.DefaultRouter()

urlpatterns = [
    re_path(r'', include(router.urls)),
    re_path('schools$',views.OrganizationView.as_view(),name='schools'),
    re_path('microsite$',views.MicrositeByOrganisation.as_view(),name='microsite'),
    re_path('users/$',views.UserRegistrationView.as_view(),name='user_reg'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses$',views.CourseView.as_view(),name='courses'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)$',views.CourseDetailsView.as_view(),name='coursedetails'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/enrolments$',views.CourseEnrollmentView.as_view(),name='enrollment'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/cohorts$',views.CohortView.as_view(),name='cohorts'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/cohort/(?P<cohort_id>[\w.@+:-]+)/users$',views.EnrollCohortView.as_view(),name='adduser_to_cohort'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/cohort/(?P<cohort_id>[\w.@+:-]+)/unenroll/users$',views.UnenrollCohortUserView.as_view(),name='remove_user_from_cohort'),
    re_path('users/(?P<userName>[\w.@+:-]+)$',views.UserDetailsView.as_view(),name='username_by_mail'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/role$',views.StaffRegistrationView.as_view(),name='access_role_for_course'),
    re_path('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/unenroll$',views.CourseUnenrollmentView.as_view(),name='unenroll_user_from_course'),
    re_path('users/(?P<userName>[\w.@+:-]+)/resetUser$',views.UserReset.as_view(),name='user_reset'),
    re_path('users/(?P<userName>[\w.@+:-]+)/resetPassword$',views.UserPasswordReset.as_view(),name='user_paswrd_reset') #### NEW
]