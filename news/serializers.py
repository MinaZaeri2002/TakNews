from django.utils.text import slugify
from rest_framework import serializers
from .models import News, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class NewsSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )

    tags_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'source', 'published_at', 'created_at', 'updated_at', 'is_active', 'tags', 'tags_info']

    def get_tags_info(self, obj):
        return TagSerializer(obj.tags.all(), many=True).data

    def create(self, validated_data):
        tag_names = validated_data.pop('tags', [])
        news = News.objects.create(**validated_data)

        for name in tag_names:
            name = name.strip()
            if name:
                tag, _ = Tag.objects.get_or_create(
                    name=name,
                    defaults={'slug': slugify(name)}
                )
                news.tags.add(tag)
        return news

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tag_names is not None:
            tags = []
            for name in tag_names:
                name = name.strip()
                if name:
                    tag, _ = Tag.objects.get_or_create(
                        name=name,
                        defaults={'slug': slugify(name)}
                    )
                    tags.append(tag)
            instance.tags.set(tags)
        return instance
