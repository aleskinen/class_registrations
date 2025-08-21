from django.shortcuts import render, get_object_or_404, redirect

from .models import Event, Contact, EventInstance, EventType, Registration, ParticipantProfile

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.contrib import messages
import random

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_events = Event.objects.all().count()
    num_instances = EventInstance.objects.all().count()

    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    # Available books (status = 'a')
    num_instances_available = EventInstance.objects.filter(status__exact='n').count()

    num_contacts = Contact.objects.count()

    context = {
        'num_events': num_events,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_contacts': num_contacts,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

from django.views import generic

class EventListView(generic.ListView):
    model = Event
    paginate_by = 10

class EventDetailView(generic.DetailView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only show event instances that are actually scheduled (have a date)
        # Show scheduled instances (have a date) plus any instances the current user is registered to,
        # even if they lack a date, so the user sees all their registrations for this event.
        context['event_instances'] = (
            EventInstance.objects.filter(event=self.object, date__isnull=False)
            .order_by('date')
        )
        # Provide a list of instance IDs the current user has registered for, for template checks
        reg_ids = []
        if self.request.user.is_authenticated:
            reg_ids = list(
                Registration.objects.filter(
                    user=self.request.user, event_instance__event=self.object
                ).values_list('event_instance_id', flat=True)
            )
        context['registered_instance_ids'] = reg_ids
        return context

class ContactListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = Contact
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_staff

class ContactDetailView(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    model = Contact

    def test_func(self):
        return self.request.user.is_staff


class UnapprovedUsersView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = ParticipantProfile
    template_name = 'events/unapproved_users.html'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return (
            ParticipantProfile.objects.select_related('user')
            .filter(approved=False)
            .order_by('user__username')
        )

    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        ids = request.POST.getlist('ids')
        approve_all = request.POST.get('approve_all')
        if approve_all:
            updated = ParticipantProfile.objects.filter(approved=False).update(approved=True)
            messages.success(request, f'Approved {updated} user(s).')
        else:
            if ids:
                updated = ParticipantProfile.objects.filter(id__in=ids, approved=False).update(approved=True)
                messages.success(request, f'Approved {updated} selected user(s).')
            else:
                messages.info(request, 'No users selected.')
        return redirect('unapproved-users')



class EventsByUserListView(LoginRequiredMixin,generic.ListView):
    """List Registrations for the current user."""
    model = Registration
    template_name = 'events/eventinstance_list_user.html'
    paginate_by = 10

    def get_queryset(self):
        profile = getattr(self.request.user, 'profile', None)
        if not profile or not profile.approved:
            return Registration.objects.none()
        return (
            Registration.objects.select_related('event_instance', 'event_instance__event')
            .filter(user=self.request.user, event_instance__status__exact='n')
            .order_by('event_instance__date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.request.user, 'profile', None)
        context['approval_pending'] = not (profile and profile.approved)
        return context


@login_required
def register_eventinstance(request, pk):
    """Register the current user to a specific EventInstance with a role, respecting capacity."""
    eventinst = get_object_or_404(EventInstance, pk=pk)
    if request.method != 'POST':
        return redirect('Event-detail', pk=eventinst.event.pk)

    if eventinst.status != 'n' or eventinst.is_past:
        return HttpResponseForbidden('Registration not allowed for this event instance.')

    role = request.POST.get('role')
    if role not in [Registration.Role.LEADER, Registration.Role.FOLLOWER, Registration.Role.DOUBLEROLE]:
        return HttpResponseForbidden('Invalid role')

    # Prevent duplicate registration per instance
    if Registration.objects.filter(user=request.user, event_instance=eventinst).exists():
        return redirect('Event-detail', pk=eventinst.event.pk)

    leaders = eventinst.leaders_count()
    followers = eventinst.followers_count()
    total = eventinst.total_count()
    maxL = eventinst.event.max_leaders
    maxF = eventinst.event.max_followers
    maxT = eventinst.event.max_participants

    if role == Registration.Role.LEADER:
        if maxL and leaders >= maxL:
            return HttpResponseForbidden('Leader capacity reached')
    elif role == Registration.Role.FOLLOWER:
        if maxF and followers >= maxF:
            return HttpResponseForbidden('Follower capacity reached')
    elif role == Registration.Role.DOUBLEROLE:
        # DoubleRole allowed if total capacity exists beyond sum of role caps
        # i.e., if max_participants > (max_leaders + max_followers) and total < max_participants
        if not maxT or maxT <= (maxL + maxF) or total >= maxT:
            return HttpResponseForbidden('DoubleRole not available')

    Registration.objects.create(user=request.user, event_instance=eventinst, role=role)

    return redirect('Event-detail', pk=eventinst.event.pk)


@login_required
def cancel_eventinstance(request, pk):
    """Cancel the current user's registration for a specific EventInstance."""
    eventinst = get_object_or_404(EventInstance, pk=pk)
    if request.method != 'POST':
        return redirect('Event-detail', pk=eventinst.event.pk)

    deleted, _ = Registration.objects.filter(user=request.user, event_instance=eventinst).delete()

    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('my-events')


def register(request):
    """Simple registration with math captcha and staff approval workflow."""
    User = get_user_model()
    errors = []
    success = False

    # Generate new captcha when missing or on GET
    if request.method == 'GET' or 'captcha_a' not in request.session or 'captcha_b' not in request.session:
        request.session['captcha_a'] = random.randint(1, 9)
        request.session['captcha_b'] = random.randint(1, 9)
    a = request.session['captcha_a']
    b = request.session['captcha_b']

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password1 = request.POST.get('password1') or ''
        password2 = request.POST.get('password2') or ''
        role = request.POST.get('role') or 'F'
        ans = request.POST.get('captcha_answer') or ''

        # Validate
        if not username:
            errors.append('Username is required')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        if not password1:
            errors.append('Password is required')
        if password1 != password2:
            errors.append('Passwords do not match')
        try:
            if int(ans) != (a + b):
                errors.append('Captcha answer is incorrect')
        except ValueError:
            errors.append('Captcha answer is required')
        if role not in [Registration.Role.LEADER, Registration.Role.FOLLOWER, Registration.Role.DOUBLEROLE]:
            errors.append('Invalid role')

        if not errors:
            user = User.objects.create_user(username=username, email=email, password=password1)
            from .models import ParticipantProfile
            ParticipantProfile.objects.create(user=user, role=role, approved=False)
            success = True
            # Reset captcha for next time
            request.session.pop('captcha_a', None)
            request.session.pop('captcha_b', None)

    return render(request, 'registration/register.html', {
        'errors': errors,
        'success': success,
        'captcha_a': a,
        'captcha_b': b,
    })
