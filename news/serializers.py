from django.utils.text import slugify
from rest_framework import serializers
from .models import News, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ('slug',)


class NewsSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    tag_names= serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = News
        fields = '__all__'
        extra_fields = ['tags_names']

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        tags_data = validated_data.pop('tags', [])

        news = News.objects.create(**validated_data)

        all_tag_names = []

        all_tag_names.extend(tag_names)

        for tag_data in tags_data:
            if 'name' in tag_data:
                all_tag_names.append(tag_data['name'])

        for tag_name in set(all_tag_names):
            tag_name = tag_name.strip()
            if tag_name:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': slugify(tag_name)}
                )
                news.tags.add(tag)

        return news

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        tags_to_add = []

        for tag_data in tags_data:
            tag_name = tag_data.get('name', '').strip()
            if tag_name:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': slugify(tag_name)}
                )
                tags_to_add.append(tag)

        instance.tags.set(tags_to_add)

        return instance



