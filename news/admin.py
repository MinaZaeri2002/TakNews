from django.contrib import admin
from django import forms
from django.contrib.auth.models import Group, User
from django.utils.text import slugify

from .models import News, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at', 'is_active')
    list_filter = ('is_active', 'tags', 'source')
    search_fields = ('title', 'content')
    filter_horizontal = ('tags',)
    date_hierarchy = 'published_at'
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'source', 'published_at', 'is_active'),
        }),
        ('tags', {
            'fields': ('tags',),
            'classes': ('collapse',),
            'description': 'Add new tags to this news.',
        }),
    )


admin.site.unregister(Group)
admin.site.unregister(User)
