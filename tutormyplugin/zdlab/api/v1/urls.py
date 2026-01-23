"""URL definitions for Zdlab API version 1
"""

from django.conf.urls import include, url
from rest_framework import routers

# Initially doing relative pathing because the full path is a mouthful and a half:
#  `openedx.core.djangoapps.appsembler.api`

from tutormyplugin.zdlab.api.v1 import views


router = routers.DefaultRouter()

urlpatterns = [
    url(r'', include(router.urls)),
    url('schools$',views.OrganizationView.as_view(),name='schools'),
    url('microsite$',views.MicrositeByOrganisation.as_view(),name='microsite'),
    url('users/$',views.UserRegistrationView.as_view(),name='user_reg'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses$',views.CourseView.as_view(),name='courses'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)$',views.CourseDetailsView.as_view(),name='coursedetails'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/enrolments$',views.CourseEnrollmentView.as_view(),name='enrollment'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/cohorts$',views.CohortView.as_view(),name='cohorts'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/cohort/(?P<cohort_id>[\w.@+:-]+)/users$',views.EnrollCohortView.as_view(),name='adduser_to_cohort'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/cohort/(?P<cohort_id>[\w.@+:-]+)/unenroll/users$',views.UnenrollCohortUserView.as_view(),name='remove_user_from_cohort'),
    url('users/(?P<userName>[\w.@+:-]+)$',views.UserDetailsView.as_view(),name='username_by_mail'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/role$',views.StaffRegistrationView.as_view(),name='access_role_for_course'),
    url('schools/(?P<school_id>[\w.@+:-]+)/courses/(?P<course_id>[\w.@+:-]+)/unenroll$',views.CourseUnenrollmentView.as_view(),name='unenroll_user_from_course'),
    url('users/(?P<userName>[\w.@+:-]+)/resetUser$',views.UserReset.as_view(),name='user_reset'),
    url('users/(?P<userName>[\w.@+:-]+)/resetPassword$',views.UserPasswordReset.as_view(),name='user_paswrd_reset') #### NEW
]