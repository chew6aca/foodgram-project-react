import base64

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Модель поля с изображением в формате base64."""

    def to_internal_value(self, data):
        """Декодирует изображение base64 в обычный формат."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


def get_shopping_list(ingredients, owner):
    """Формирует содержимое файла со списком покупок."""
    header = (
        f'Список покупок.\nВладелец: {owner.first_name} {owner.last_name}.\n'
    )
    shopping_list = '\n'.join(
        [
            f'- {ingredient["ingredient__name"]} '
            f' ({ingredient["ingredient__measurement_unit"]})'
            f' {ingredient["amount"]} '
            for ingredient in ingredients
        ]
    )
    return header + shopping_list
