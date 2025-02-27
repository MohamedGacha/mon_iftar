from django.contrib import admin

from .models import Beneficiaire, Benevole, Location


class BenevoleAdmin(admin.ModelAdmin):
    list_display = ('username', 'num_benevole', 'is_first_loggin',
                    'point_distribution', 'admin')  # Display the fields in the list view
    # Allow searching by username or num_benevole
    search_fields = ('username', 'num_benevole')
    # Add filters for easier admin management
    list_filter = ('is_first_loggin', 'admin')

    # Allow editing of the is_first_loggin field directly in the admin panel
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'num_benevole', 'num_telephone', 'point_distribution', 'is_first_loggin', 'admin')
        }),
    )


admin.site.register(Benevole, BenevoleAdmin)

admin.site.register(Beneficiaire)
admin.site.register(Location)
