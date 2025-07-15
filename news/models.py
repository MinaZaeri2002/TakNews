from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField(max_length=250)
    content = models.TextField()
    source = models.URLField(unique=True)
    tags = models.ManyToManyField(Tag, blank=True)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_short_content(self, length=100):
        if len(self.content) > length:
            return self.content[:length] + '...'
        return self.content
