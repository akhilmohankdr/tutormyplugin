"""Zdlab version 1 API views

Only include view classes here. See the tests/test_permissions.py:get_api_classes()
method.
"""
import logging
import six

from django.conf import settings
import django.contrib.sites.shortcuts
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.apps import apps
from django.db.models import Q


from common.djangoapps.util.json_request import JsonResponse


from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView 


from openedx.core.djangoapps.enrollments import api
from openedx.core.djangoapps.user_api.models import UserRetirementRequest

from openedx.core.djangoapps.course_groups.cohorts import add_cohort,get_group_info_for_cohort,get_assignment_type,add_user_to_cohort,get_cohort_by_id,get_course_cohorts,remove_user_from_cohort
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.enrollments.api import get_course_enrollment_details
from openedx.core.lib.exceptions import CourseNotFoundError
from openedx.core.djangoapps.enrollments.paginators import CourseEnrollmentsApiListPagination
from openedx.core.djangoapps.enrollments.serializers import CourseEnrollmentsApiListSerializer
from openedx.core.djangolib.js_utils import dump_js_escaped_json
from tutormyplugin.zdlab.api.v1.constants import school_not_found_response_data,course_not_found_for_school_response_data

from lms.djangoapps.courseware.courses import get_course,check_course_access_with_redirect,get_course_by_id


from opaque_keys.edx.keys import CourseKey

from social_django import models as social_models

from student.models import CourseEnrollment, CourseAccessRole , UserProfile

from organizations.api import (
    add_organization,
    add_organization_course,
    get_organization_by_short_name,
    get_organization_courses,
    get_organizations
)

from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.django_comment_common.models import assign_role
#from common.djangoapps.student.models import CourseAccessRole

from openedx.core.djangoapps.enrollments.errors import (
    CourseEnrollmentClosedError,
    CourseEnrollmentExistsError,
    CourseEnrollmentFullError,
    InvalidEnrollmentAttribute,
    UserNotFoundError
)

from student.models import (
    AlreadyEnrolledError,
    CourseEnrollment,
    CourseEnrollmentAttribute,
    CourseFullError,
    EnrollmentClosedError,
    NonExistentCourseError
)

from openedx.core.djangoapps.enrollments.serializers import CourseEnrollmentSerializer
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


def unlink_cohort_partition_group(cohort):
    """
    Remove any existing cohort to partition_id/group_id link.
    """
    CourseUserGroupPartitionGroup.objects.filter(course_user_group=cohort).delete()

def _get_cohort_representation(cohort, course):
    """
    Returns a JSON representation of a cohort.
    """
    group_id, partition_id = get_group_info_for_cohort(cohort)
    assignment_type = get_assignment_type(cohort)
    return {
        'name': cohort.name,
        'id': cohort.id,
        'user_count': cohort.users.filter(courseenrollment__course_id=course.location.course_key,
                                          courseenrollment__is_active=1).count(),
        'assignment_type': assignment_type,
        'user_partition_id': partition_id,
        'group_id': group_id,
    }

def check_course_access_with_redirect(course, user, action, check_if_enrolled=False, check_survey_complete=True, check_if_authenticated=False):  # lint-amnesty, pylint: disable=line-too-long
    """
    Check that the user has the access to perform the specified action
    on the course (CourseDescriptor|CourseOverview).

    check_if_enrolled: If true, additionally verifies that the user is enrolled.
    check_survey_complete: If true, additionally verifies that the user has completed the survey.
    """
    request = get_current_request()
    check_content_start_date_for_masquerade_user(course.id, user, request, course.start)

    access_response = check_course_access(course, user, action, check_if_enrolled, check_survey_complete, check_if_authenticated)  # lint-amnesty, pylint: disable=line-too-long

    if not access_response:
        # Redirect if StartDateError
        if isinstance(access_response, StartDateError):
            start_date = strftime_localized(course.start, 'SHORT_DATE')
            params = QueryDict(mutable=True)
            params['notlive'] = start_date
            raise CourseAccessRedirect('{dashboard_url}?{params}'.format(
                dashboard_url=reverse('dashboard'),
                params=params.urlencode()
            ), access_response)

        # Redirect if AuditExpiredError
        if isinstance(access_response, AuditExpiredError):
            params = QueryDict(mutable=True)
            params['access_response_error'] = access_response.additional_context_user_message
            raise CourseAccessRedirect('{dashboard_url}?{params}'.format(
                dashboard_url=reverse('dashboard'),
                params=params.urlencode()
            ), access_response)

        # Redirect if the user must answer a survey before entering the course.
        if isinstance(access_response, MilestoneAccessError):
            raise CourseAccessRedirect('{dashboard_url}'.format(
                dashboard_url=reverse('dashboard'),
            ), access_response)

        # Redirect if the user is not enrolled and must be to see content
        if isinstance(access_response, EnrollmentRequiredAccessError):
            raise CourseAccessRedirect(reverse('about_course', args=[str(course.id)]))

        # Redirect if user must be authenticated to view the content
        if isinstance(access_response, AuthenticationRequiredAccessError):
            raise CourseAccessRedirect(reverse('about_course', args=[str(course.id)]))

        # Redirect if the user must answer a survey before entering the course.
        if isinstance(access_response, SurveyRequiredAccessError):
            raise CourseAccessRedirect(reverse('course_survey', args=[str(course.id)]))

        # Deliberately return a non-specific error message to avoid
        # leaking info about access control settings
        raise CoursewareAccessException(access_response)

def get_course_with_access(user, action, course_key, depth=0, check_if_enrolled=False, check_survey_complete=True, check_if_authenticated=False):  # lint-amnesty, pylint: disable=line-too-long

    course = get_course_by_id(course_key, depth)
    return course

def _get_course_with_access(request, course_key_string, action='staff'):
    """
    Fetching a course with expected permission level
    """
    course_key = CourseKey.from_string(course_key_string)
    return course_key, get_course_with_access(request.user, action, course_key)

def strip_if_string(value):
    if isinstance(value, six.string_types):
        return value.strip()
    return value

def is_valid_school(username_or_email):   
    username_or_email = strip_if_string(username_or_email)
    # there should be one user with either username or email equal to username_or_email
    user = User.objects.get(Q(email=username_or_email) | Q(username=username_or_email))
    if user.username == username_or_email:
        UserRetirementRequest = apps.get_model('user_api', 'UserRetirementRequest')
        if UserRetirementRequest.has_user_requested_retirement(user):
            raise User.DoesNotExist
    return user


def checkoganization(school_id):
        org = school_id
        try:
            organization = get_organization_by_short_name(org)
        except Exception as e:
            logging.error(str(e))
            return False
        return True

def is_school_have_course(school_id):
    if(checkoganization(school_id)==True):
        school_have_course = get_organization_courses(get_organization_by_short_name(school_id))
        if(school_have_course != []):
            return True
        else:
             return course_not_found_for_school_response_data
    else:
        return school_not_found_response_data

def get_course_enrollment(username, course_id):
    
    course_key = CourseKey.from_string(course_id)
    try:
        enrollment = CourseEnrollment.objects.get(
            user__username=username, course_id=course_key
        )
        return CourseEnrollmentSerializer(enrollment).data
    except CourseEnrollment.DoesNotExist:
        return None


def _update_enrollment(enrollment, is_active=None, mode=None):
    enrollment.update_enrollment(is_active=is_active, mode=mode)
    enrollment.save()
    return CourseEnrollmentSerializer(enrollment).data

def create_course_enrollment(username, course_id, mode, is_active):
    course_key = CourseKey.from_string(course_id)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        #msg = u"Not user with username '{username}' found.".format(username=username)
        #log.warning(msg)
        raise UserNotFoundError(msg)  # lint-amnesty, pylint: disable=raise-missing-from

    try:
        enrollment = CourseEnrollment.enroll(user, course_key, check_access=False) #can_upgrade=False
        return _update_enrollment(enrollment, is_active=is_active, mode=mode)
    except NonExistentCourseError as err:
        raise CourseNotFoundError(text_type(err))  # lint-amnesty, pylint: disable=raise-missing-from
    except EnrollmentClosedError as err:
        raise CourseEnrollmentClosedError(text_type(err))  # lint-amnesty, pylint: disable=raise-missing-from
    except CourseFullError as err:
        raise CourseEnrollmentFullError(text_type(err))  # lint-amnesty, pylint: disable=raise-missing-from
    except AlreadyEnrolledError as err:
        enrollment = get_course_enrollment(username, course_id)
        raise CourseEnrollmentExistsError(text_type(err), enrollment)  # lint-amnesty, pylint: disable=raise-missing-from

class MicrositeByOrganisation(APIView):
    def post(self, request, *args, **kwargs):
        organisation = request.data.get('organisation')
        configuration = SiteConfiguration.get_configuration_for_org(organisation, select_related=['site'])
        response_data = {'message': str(configuration.site)}
        return Response(response_data, status=200)

class BulkCourseUnenrollmentView(APIView):
    def post(self, request,**kwargs):
        school_id = self.kwargs['school_id']
        course_id = self.kwargs['course_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            try:
                usernames = request.data.get('username')
                for username in usernames:
                    user = User.objects.get(username=username)
                    course_key = CourseLocator.from_string(course_id)
                    CourseEnrollment.unenroll(user, course_id)
                response_data = {'message': 'The  given user having usernames ' + str(usernames) + ' is unenrolled now for ' + str(course_id) + ' in ' + school_id}
                return Response(response_data, status=200)

            except Exception as e:
                logging.error(str(e))
                response_data = {'message': 'user unenrollment failed'}
                return Response(response_data, status=404)
        else:
            return Response(is_valid_scholl_and_course_response, status=404)

class BulkCourseEnrollmentView(ListAPIView):
    serializer_class = CourseEnrollmentsApiListSerializer
    pagination_class = CourseEnrollmentsApiListPagination
    #@csrf_exempt
    def post(self,request,**kwargs):
        school_id = kwargs['school_id']
        course_id = kwargs['course_id']
        usernames = request.data.get('usernames')
        mode=None
        is_active=True
        #enrollment_attributes=None
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            for username in usernames:
                response = create_course_enrollment(
                            username,
                            six.text_type(course_id),
                            mode=mode,
                            is_active=is_active,
                            #enrollment_attributes=enrollment_attributes
                        )
            response = {'message':'all users enrolled'}
            return Response(response, status=200)
        else:
            return Response(is_valid_scholl_and_course_response, status=404)

class CourseUnenrollmentView(APIView):
    def post(self, request,**kwargs):
        school_id = self.kwargs['school_id']
        course_id = self.kwargs['course_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            try:
                username = request.data.get('username')
                user = User.objects.get(username=username)
                course_key = CourseLocator.from_string(course_id)
                CourseEnrollment.unenroll(user, course_id)
                response_data = {'message': 'The  given user having username ' + username + ' is unenrolled now for ' + str(course_id) + ' in ' + school_id}
                return Response(response_data, status=200)

            except Exception as e:
                logging.error(str(e))
                response_data = {'message': 'user unenrollment failed'}
                return Response(response_data, status=404)
        else:
            return Response(is_valid_scholl_and_course_response, status=404)


#Gets details of speciifed course from LMS,return course details like course-id,course-name,mode etc
class CourseDetailsView(APIView):
    
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        course_id = kwargs['course_id']
        school_id = kwargs['school_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            try:
                return Response(get_course_enrollment_details(course_id=course_id))
            except CourseNotFoundError:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "message": (
                            u"No course found for course ID '{course_id}'"
                        ).format(course_id=course_id)
                    }
                )
        else:
            return Response(is_valid_scholl_and_course_response, status=404)


#Add users to the specified cohort
class EnrollCohortView(APIView):

    def _get_course_and_cohort(self, request, course_key_string, cohort_id):
        course_key, _ = _get_course_with_access(request, course_key_string)

        try:
            cohort = get_cohort_by_id(course_key, cohort_id)
        except:
            msg = u'Cohort (ID {cohort_id}) not found for {course_key_string}'.format(
                cohort_id=cohort_id,
                course_key_string=course_key_string
            )
            raise self.api_error(status.HTTP_404_NOT_FOUND, msg, 'cohort-not-found')  # lint-amnesty, pylint: disable=raise-missing-from
        return course_key, cohort

    def post(self, request,**kwargs):
        username = None
        cohort_id = kwargs['cohort_id']
        course_key_string = kwargs['course_id']
        school_id = kwargs['school_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            #TODO properly check whether the school have course_id equal to input course id. currently the list have only one course.
            #Do proper looping and checking corresponding to the output of is_school_have_course
            _, cohort = self._get_course_and_cohort(request, course_key_string, cohort_id)
            users = request.data.get('users')
            if not users:
                if username is not None:
                    users = [username]
                else:
                    raise self.api_error(status.HTTP_400_BAD_REQUEST, 'Missing users key in payload', 'missing-users')

            added, changed, present, unknown, preassigned, invalid = [], [], [], [], [], []
            for username_or_email in users:
                if not username_or_email:
                    continue

                try:
                    # A user object is only returned by add_user_to_cohort if the user already exists.
                    (user, previous_cohort, preassignedCohort) = add_user_to_cohort(cohort, username_or_email)

                    if preassignedCohort:
                        preassigned.append(username_or_email)
                    elif previous_cohort:
                        info = {
                            'email': user.email,
                            'previous_cohort': previous_cohort,
                            'username': user.username
                        }
                        changed.append(info)
                    else:
                        info = {
                            'username': user.username,
                            'email': user.email
                        }
                        added.append(info)
                except User.DoesNotExist:
                    unknown.append(username_or_email)
                except ValidationError:
                    invalid.append(username_or_email)
                except ValueError:
                    present.append(username_or_email)

            return Response({
                'success': True,
                'added': added,
                'changed': changed,
                'present': present,
                'unknown': unknown,
                'preassigned': preassigned,
                'invalid': invalid
            })
        else:
            return Response(is_valid_scholl_and_course_response, status=404)

class UnenrollCohortUserView(APIView):
    def _get_course_and_cohort(self, request, course_key_string, cohort_id):
        course_key, _ = _get_course_with_access(request, course_key_string)

        try:
            cohort = get_cohort_by_id(course_key, cohort_id)
        except:
            msg = u'Cohort (ID {cohort_id}) not found for {course_key_string}'.format(
                cohort_id=cohort_id,
                course_key_string=course_key_string
            )
            raise self.api_error(status.HTTP_404_NOT_FOUND, msg, 'cohort-not-found')  # lint-amnesty, pylint: disable=raise-missing-from
        return course_key, cohort

    def post(self, request,**kwargs):
        username = None
        cohort_id = kwargs['cohort_id']
        course_key_string = kwargs['course_id']
        school_id = kwargs['school_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            #TODO properly check whether the school have course_id equal to input course id. currently the list have only one course.
            #Do proper looping and checking corresponding to the output of is_school_have_course
            _, cohort = self._get_course_and_cohort(request, course_key_string, cohort_id)
            users = request.data.get('users')
            if not users:
                if username is not None:
                    users = [username]
                else:
                    raise self.api_error(status.HTTP_400_BAD_REQUEST, 'Missing users key in payload', 'missing-users')

            for username_or_email in users:
                if not username_or_email:
                    continue

                try:
                    data = remove_user_from_cohort(cohort, username_or_email)  
                
                except Exception as e:
                    logging.error(str(e))
                    response_data = {'message': 'The given data is not valid'}
                    return Response(response_data, status=404)
                
            response_data = {
                    'message': 'successfully changed user details',
                    'data': str(data)
                            }
            return Response(response_data, status=200)


        else:
            return Response(is_valid_scholl_and_course_response, status=404)




#GET---list all the cohorts assaigned to a course
#POST---Create a new cohort for a course
#Gets all cohorts present in the specified course
#Creates a new cohort in the specified course
class CohortView(APIView):
    authentication_classes = []
    def _get_course_and_cohort(self, request, course_key_string, cohort_id):
        """
        Return the course and cohort for the given course_key_string and cohort_id.
        """
        course_key, _ = _get_course_with_access(request, course_key_string)

        try:
            cohort = get_cohort_by_id(course_key, cohort_id)
        except:
            msg = u'Cohort (ID {cohort_id}) not found for {course_key_string}'.format(
                cohort_id=cohort_id,
                course_key_string=course_key_string
            )
            raise self.api_error(status.HTTP_404_NOT_FOUND, msg, 'cohort-not-found')  # lint-amnesty, pylint: disable=raise-missing-from
        return course_key, cohort
    
    def post(self,request, *args, **kwargs):
        name = request.data.get('name')
        school_id = kwargs['school_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            course_id = kwargs['course_id']
            course_key = CourseKey.from_string(course_id)
            course = get_course(course_key)
            cohort = add_cohort(course_key, name, assignment_type='manual')
            existing_group_id, _ = get_group_info_for_cohort(cohort)
            if existing_group_id is not None:
                unlink_cohort_partition_group(cohort)
            return JsonResponse(_get_cohort_representation(cohort, course))
        else:
            return Response(is_valid_scholl_and_course_response, status=404)


    def get(self, request, *args, **kwargs):
        course_id = kwargs['course_id']
        school_id = kwargs['school_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            data = get_course_cohorts(course=None, course_id=course_id, assignment_type=None) #TODO remove course name hard coding
            response_data = {
                'message': 'cohorts for the given course is',
                'cohorts': [cohort.name for cohort in data]
            } 
            return Response(response_data, status=200)
        else:
            return Response(is_valid_scholl_and_course_response, status=404)


class UserReset(APIView):
    def post(self, request, *args, **kwargs):
        new_email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        status = request.data.get('status')
        username=kwargs['userName']
        try:
            user = User.objects.get(username=username)
            user.email = new_email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = status
            user.save()
            response_data = {
                'message': 'successfully changed user details',
                'user': str(user)
                            }
            return Response(response_data, status=200)

        except Exception as e:
            logging.error(str(e))
            response_data = {'message': 'The given username is not a valid one or new password is not acceptable'}
            return Response(response_data, status=404)


#Reset password of user.
class UserPasswordReset(APIView):
    def post(self, request, *args, **kwargs):
        new_password = request.data.get('new_password')
        username=kwargs['userName']
        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            response_data = {
            'message': 'successfully changed user password',
            'user': str(user)
                            }
            return Response(response_data, status=200)

        except Exception as e:
            logging.error(str(e))
            response_data = {'message': 'The given username is not a valid one or new password is not acceptable'}
            return Response(response_data, status=404)



#GET----All the enrolled user for a course
#Gets users enrolled in a speciifed course from LMS
#POST---Enrols learners into the speciifed course in LMS
class CourseEnrollmentView(ListAPIView):
    serializer_class = CourseEnrollmentsApiListSerializer
    pagination_class = CourseEnrollmentsApiListPagination
    #@csrf_exempt
    def post(self,request,**kwargs):
        school_id = kwargs['school_id']
        course_id = kwargs['course_id']
        username = request.data.get('username')
        mode=None
        is_active=True
        #enrollment_attributes=None
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            response = create_course_enrollment(
                        username,
                        six.text_type(course_id),
                        mode=mode,
                        is_active=is_active,
                        #enrollment_attributes=enrollment_attributes
                    )
            return Response(response, status=200)
        else:
            return Response(is_valid_scholl_and_course_response, status=404)


    def list(self, request, *args, **kwargs):
        school_id = self.kwargs['school_id']
        course_id = self.kwargs['course_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            enrollments = CourseEnrollment.objects.filter(course_id=course_id,is_active=True).order_by('created')
            serializer = CourseEnrollmentsApiListSerializer(enrollments, many=True)
            return Response(serializer.data)
        else:
            return Response(is_valid_scholl_and_course_response, status=404)


#Gets all courses assigned to an organization
class CourseView(ListAPIView):
    def get(self, request, *args, **kwargs):
        school_id = kwargs['school_id']
        if(checkoganization(school_id)==True):
            response = get_organization_courses(get_organization_by_short_name(school_id))
            if (response != []):
                temp_response = []
                for res in response:
                    res.pop('logo')
                    temp_response.append(res)
                response_data = {
                    'message': 'successfully obtained course of a organisation',
                    'response': temp_response
                    }
                return Response(response_data, status=200)
            else:
                response_data = {
                    'message': 'The given school have no subscription to any course',
                    'response': str(response)
                    }
                return Response(response_data, status=404)

        else:
            return Response(school_not_found_response_data, status=404)

#Get and post organisation
class OrganizationView(APIView):
    """Verify Organization listing behavior."""
    #Gets all sites from LMS
    def get(self, request, *args, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """Returns organization list as json."""
        organizations = get_organizations()
        logging.error("the organisations were :" + str(organizations))
        org_names_list = [{"name":org["name"],"short_name":org["short_name"],"id":org["id"]} for org in organizations]
        return HttpResponse(dump_js_escaped_json(org_names_list), content_type='application/json; charset=utf-8')  # lint-amnesty, pylint: disable=http-response-with-content-type-json
            
    #Creates a new site in LMS
    def post(self, request):
        try:
            add_organization(organization_data={
                    'name': request.data.get('displayName'),
                    'short_name': request.data.get('short_name'),
                    'description': request.data.get('description'),
                })
            response_data = {
                'message': 'successfully created school',
                'data': request.data
            }
            return Response(response_data, status=200)
        except Exception as e:
            logging.error(str(e))
            response_data = {'message': 'The given organisation already exist or input json currupted'}
            return Response(response_data, status=404)

            

#By passing in the email, get the details about the user from LMS 
class UserDetailsView(APIView):
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        username=kwargs['userName']
        try:
            user = is_valid_school(username)
            response_data = {
                'message': 'successfully obtained user data',
                'user': str(user)
            }
            return Response(response_data, status=200)

        except Exception as e:
            logging.error(str(e))
            response_data = {'message': 'The  given username is not a valid one'}
            return Response(response_data, status=404)


        

class UserRegistrationView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        country = request.data.get('country')
        try:
            user = User.objects.create_user(username=username, password=password, email = email, first_name=first_name, last_name=last_name)
            user.is_active = True
            user.save()
            profile = UserProfile(
            user=user,
            **{"country": country, "language": "English"}
            )
            profile.save()
            user_id = user.id
            return Response({'message':'user added to LMS','user_id': user_id}, status=200)
        except Exception as e:
            logging.error(str(e))
            response_data = {'message': 'user registartion failed'}
            return Response(response_data, status=404)

class StaffRegistrationView(APIView):
    def post(self, request,**kwargs):
        school_id = self.kwargs['school_id']
        course_id = self.kwargs['course_id']
        is_valid_scholl_and_course_response =  is_school_have_course(school_id)
        if(is_valid_scholl_and_course_response == True):
            try:
                username = request.data.get('username')
                role = request.data.get('role')

                user = User.objects.get(username=username)
                course_key = CourseLocator.from_string(course_id)
                logging.error("the course key is " + str(course_key))
                CourseAccessRole.objects.update_or_create(user=user, course_id=course_key, org=school_id, role=role)
                response_data = {'message': 'The  given user having username ' + username + ' is ' +role+ ' now for ' + str(course_id) + ' in ' + school_id}
                return Response(response_data, status=200)
            except Exception as e:
                logging.error(str(e))
                response_data = {'message': 'user role registartion failed'}
                return Response(response_data, status=404)
        else:
            return Response(is_valid_scholl_and_course_response, status=404)




"""class CheckOrganisation(APIView):
    def get(self, request, *args, **kwargs):
        org = kwargs['school_id']
        organization ={}
        try:
            organization = get_organization_by_short_name(org)
        except Exception as e:
            logging.error(str(e))
            response_data = {
            'message': 'the given short name for school is not valid',
            'status': 404
            }
            return Response(response_data, status=200)
        response_data = {
            'message': 'successfully obtained organisation',
            'data': str(organization),
            'status':200
        }
        return Response(response_data, status=200)
class AddCourseToOrganisation(APIView):
    def post(self,request,**kwargs):
        course_key_string = kwargs['course_id']
        school_id = kwargs['school_id']
        organization = get_organization_by_short_name(school_id)
        add_organization_course(organization_data=organization, course_key=six.text_type(course_key_string))
        #res=add_organization_course(school_id, course_key_string)
        response_data = {
            'message': 'successfully added course to organisation',
            'data': str(organization)
        }
        return Response(response_data, status=200)
class OrgCoursesView(APIView):
    def get(self, request, *args, **kwargs):
        school_id = kwargs['school_id']
        response = get_organization_courses(get_organization_by_short_name(school_id))
        response_data = {
            'message': 'successfully obtained course of a organisation',
            'data': str(response)
        }
        return Response(response_data, status=200)"""