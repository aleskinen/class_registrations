from django.shortcuts import render

from .models import Event, Contact, EventInstance, EventType

from django.contrib.auth.mixins import LoginRequiredMixin

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

class ContactListView(generic.ListView):
    model = Contact
    paginate_by = 10

class ContactDetailView(generic.DetailView):
    model = Contact



class EventsByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = EventInstance
    template_name = 'events/eventinstance_list_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            EventInstance.objects.filter(user=self.request.user)
            .filter(status__exact='n')
            .order_by('date')
        )
