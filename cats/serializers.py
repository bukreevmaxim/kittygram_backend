import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
import webcolors


import datetime as dt

from .models import Achievement, AchievementCat, Cat


class Hex2NameColor(serializers.Field):
    """Кастомное поле цвета.

    Принимает HEX-код цвета (например, "#b03060"),
    конвертирует его в название цвета (например, "maroon").

    Если для HEX-кода нет названия в библиотеке webcolors,
    выбрасывает ValidationError 'Для этого цвета нет имени'.
    """

    def to_representation(self, value):
        return value
    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class AchievementSerializer(serializers.ModelSerializer):
    """Сериализатор достижения.

    Переименовывает поле 'name' модели Achievement
    в 'achievement_name' для JSON-ответа.
    """

    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class Base64ImageField(serializers.ImageField):
    """Поле картинки, принимающее base64-строку (Data URI).

    Если пришла строка вида 'data:image/png;base64,...' —
    декодирует её в файл (ContentFile) с расширением из MIME-типа.
    Обычные загруженные файлы передаются без изменений.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CatSerializer(serializers.ModelSerializer):
    """Сериализатор котика.

    Добавляет вычисляемое поле 'age' (только для чтения),
    вложенный сериализатор достижений, поле цвета с конвертацией
    HEX → название и поле картинки, принимающее base64.

    'owner' — только для чтения (заполняется во ViewSet
    через perform_create).
    """

    achievements = AchievementSerializer(required=False, many=True)
    color = Hex2NameColor()
    age = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Cat
        fields = (
            'id', 'name', 'color', 'birth_year', 'achievements', 'owner', 'age',
            'image'
            )
        read_only_fields = ('owner',)

    def get_age(self, obj):
        """Возвращает возраст кота в годах: текущий год минус birth_year."""
        return dt.datetime.now().year - obj.birth_year
    
    def create(self, validated_data):
        """Создаёт кота вместе со связанными достижениями.

        Достижения ищутся по имени (get_or_create — без дублей),
        затем связываются с котом через промежуточную модель
        AchievementCat. Если достижения не переданы, кот
        создаётся без них.
        """
        if 'achievements' not in self.initial_data:
            cat = Cat.objects.create(**validated_data)
            return cat
        else:
            achievements = validated_data.pop('achievements')
            cat = Cat.objects.create(**validated_data)
            for achievement in achievements:
                current_achievement, status = Achievement.objects.get_or_create(
                    **achievement
                    )
                AchievementCat.objects.create(
                    achievement=current_achievement, cat=cat
                    )
            return cat
    
    def update(self, instance, validated_data):
        """Обновляет кота.

        Поля, не переданные в запросе, сохраняют прежние значения
        (validated_data.get с fallback на старое значение).
        Если переданы достижения — заменяет их набор у кота:
        каждое достижение ищется/создаётся по имени,
        привязка выполняется через .set().
        """
        instance.name = validated_data.get('name', instance.name)
        instance.color = validated_data.get('color', instance.color)
        instance.birth_year = validated_data.get(
            'birth_year', instance.birth_year
            )
        instance.image = validated_data.get('image', instance.image)
        if 'achievements' in validated_data:
            achievements_data = validated_data.pop('achievements')
            lst = []
            for achievement in achievements_data:
                current_achievement, status = Achievement.objects.get_or_create(
                    **achievement
                    )
                lst.append(current_achievement)
            instance.achievements.set(lst)

        instance.save()
        return instance