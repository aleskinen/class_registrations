from django.db import models

from django.urls import reverse # Used in get_absolute_url() to get URL for specified ID

from django.db.models import UniqueConstraint # Constrains fields to unique values
from django.db.models.functions import Lower # Returns lower cased value of field

from django.conf import settings
from datetime import date

class EventType(models.Model):
    """Model representing a event type."""
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="What type of event is this"
    )

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a particular EventType instance."""
        return reverse('EventType-detail', args=[str(self.id)])

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='EventType_name_case_insensitive_unique',
                violation_error_message = "Event type already exists (case insensitive match)"
            ),
        ]

class Event(models.Model):
    """Model representing a Event (but not a specific instance of a Event)."""
    title = models.CharField(max_length=200)
    contact = models.ForeignKey('Contact', on_delete=models.RESTRICT, null=True)
    # Foreign Key used because Event can only have one contact, but contacts can have multiple Events.
    # contact as a string rather than object because it hasn't been declared yet in file.

    summary = models.TextField(
        max_length=1000, help_text="Enter a brief description of the Event")

    # ManyToManyField used because event type can contain many Events. Events can cover many event types.
    # EventType class has already been defined so we can specify the object above.
    type = models.ManyToManyField(
        EventType, help_text="Select a type for this Event")
    
    def __str__(self):
        """String for representing the Model object."""
        return self.title
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this Event."""
        return reverse('Event-detail', args=[str(self.id)])
    
    def display_type(self):
        """Create a string for the type. This is required to display type in Admin."""
        return ', '.join(type.name for type in self.type.all()[:3])
        

    display_type.short_description = 'Type'

    
import uuid # Required for unique book instances

class EventInstance(models.Model):
    
    """Model representing an instance copy of a event."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
        help_text="Unique ID for this particular event across whole registry")
    event = models.ForeignKey('Event', on_delete=models.RESTRICT, null=True)
    description = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_past(self):
        """Determines if the book is overdue based on due date and current date."""
        return bool(self.date and date.today() > self.date)
    
    EVENT_STATUS = (
        ('n', 'Normal'),
        ('c', 'Canceled'),
        ('p', 'Pending'),
    )
    
    status = models.CharField(
        max_length=1,
        choices=EVENT_STATUS,
        blank=True,
        default='n',
        help_text='Event status',
    )
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.event.title if self.event else "No Event"})'

class Contact(models.Model):
    """Model representing an Contact."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def get_absolute_url(self):
        """Returns the URL to access a particular contact instance."""
        return reverse('Contact-detail', args=[str(self.id)])
    
    def __str__(self):
        """String for representing the Model object."""
        return f'{self.last_name}, {self.first_name}'

