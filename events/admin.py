from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Event, Contact, EventType, EventInstance, Registration, ParticipantProfile

# Register your models here.
#admin.site.register(Event)
# admin.site.register(Contact)
admin.site.register(EventType)
#admin.site.register(EventInstance)

# ParticipantProfile admin with approve action
class ParticipantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'approved')
    list_filter = ('approved', 'role')
    search_fields = ('user__username', 'user__email')
    actions = ['approve_profiles']

    def approve_profiles(self, request, queryset):
        updated = queryset.filter(approved=False).update(approved=True)
        self.message_user(request, f"Approved {updated} user(s).", level=messages.SUCCESS)
    approve_profiles.short_description = 'Approve selected profiles'

admin.site.register(ParticipantProfile, ParticipantProfileAdmin)

# Define the admin class
class ContactAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email')
    fields = ['first_name', 'last_name', ('phone', 'email')]

# Register the admin class with the associated model
admin.site.register(Contact, ContactAdmin)

class EventInstanceInline(admin.TabularInline):
    model = EventInstance
    extra = 0
    fields = ('date', 'description', 'status')
    show_change_link = True

# Register the Admin classes for Event using the decorator
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'contact', 'display_type', 'max_leaders', 'max_followers', 'max_participants')
    fieldsets = (
        (None, {
            'fields': ('title', 'contact', 'summary', 'type')
        }),
        ('Capacity', {
            'fields': ('max_leaders', 'max_followers', 'max_participants')
        })
    )

# Register the Admin classes for EventInstance using the decorator
class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    fields = ('user', 'role')

# Extend User admin to add an action to approve user profiles
class CustomUserAdmin(UserAdmin):
    actions = ['approve_users']
    list_display = UserAdmin.list_display + ('approved_status',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('profile')

    def approved_status(self, obj):
        profile = getattr(obj, 'profile', None)
        return bool(profile and profile.approved)
    approved_status.boolean = True
    approved_status.short_description = 'Approved'

    def approve_users(self, request, queryset):
        from .models import ParticipantProfile
        count = 0
        for user in queryset:
            profile, created = ParticipantProfile.objects.get_or_create(user=user)
            if not profile.approved:
                profile.approved = True
                profile.save()
                count += 1
        self.message_user(request, f"Approved {count} user(s).", level=messages.SUCCESS)
    approve_users.short_description = 'Approve selected users'

# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(EventInstance)
class EventInstanceAdmin(admin.ModelAdmin):
    list_display = ('event', 'date', 'status')
    list_filter = ('status', 'date')
    fieldsets = (
        (None, {
            'fields': ('event', 'date', 'description')
        }),
        ('Details', {
            'fields': ('status', 'id')
        }),
    )
    inlines = [RegistrationInline]
