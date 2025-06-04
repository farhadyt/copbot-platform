from django.contrib import admin
from .models import Mirror, Target

@admin.register(Mirror)
class MirrorAdmin(admin.ModelAdmin):
    list_display = ['codename', 'pilot', 'mirror_type', 'state', 'sync_count', 'success_rate']
    list_filter = ['mirror_type', 'state', 'pilot']
    search_fields = ['codename', 'pilot__username']

@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ['alias', 'beacon_id', 'mirror', 'echoes_captured', 'is_tracking']
    list_filter = ['is_tracking', 'mirror']
    search_fields = ['beacon_id', 'alias']