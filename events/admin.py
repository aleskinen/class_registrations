from django.contrib import admin

from .models import Event, Contact, EventType, EventInstance

# Register your models here.
#admin.site.register(Event)
# admin.site.register(Contact)
admin.site.register(EventType)
#admin.site.register(EventInstance)

# Define the admin class
class ContactAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email')
    fields = ['first_name', 'last_name', ('phone', 'email'), 'user']

# Register the admin class with the associated model
admin.site.register(Contact, ContactAdmin)

class EventInstanceInline(admin.TabularInline):
    model = EventInstance

# Register the Admin classes for Event using the decorator
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'contact', 'display_type')
    inlines = [EventInstanceInline]

# Register the Admin classes for EventInstance using the decorator
@admin.register(EventInstance)
class EventInstanceAdmin(admin.ModelAdmin):
    list_display = ('event', 'date', 'status', 'user')
    list_filter = ('status', 'date', 'user')
    fieldsets = (
        (None, {
            'fields': ('event', 'date', 'description', 'user')
        }),
        ('Details', {
            'fields': ('status', 'id')
        }),
    )
