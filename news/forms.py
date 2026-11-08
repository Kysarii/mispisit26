import re
from urllib.parse import urlsplit

from django import forms


class NewsForm(forms.Form):
    title = forms.CharField(
        label="Заголовок",
        max_length=160,
        help_text="Коротко о главном. До 160 символов.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Что произошло?", "autofocus": True}),
        error_messages={"required": "Укажите заголовок новости."},
    )
    channel_name = forms.CharField(
        label="Название канала",
        max_length=80,
        help_text="Название источника в списке публикаций.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Например, Новости технологий"}),
        error_messages={"required": "Укажите название Telegram-канала."},
    )
    source_url = forms.URLField(
        label="Ссылка на публикацию",
        max_length=300,
        assume_scheme="https",
        help_text="Публичная публикация: https://t.me/channel/123",
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://t.me/channel/123"}),
        error_messages={
            "required": "Добавьте ссылку на публикацию в Telegram.",
            "invalid": "Введите корректную ссылку вида https://t.me/channel/123.",
        },
    )
    body = forms.CharField(
        label="Текст новости",
        max_length=10000,
        help_text="Текст публикации или краткое содержание. До 10 000 символов.",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 8, "placeholder": "Расскажите о новости…"}),
        error_messages={"required": "Добавьте текст новости."},
    )

    def clean_source_url(self):
        parts = urlsplit(self.cleaned_data["source_url"])
        match = re.fullmatch(r"/([A-Za-z][A-Za-z0-9_]{4,31})/([1-9][0-9]*)/?", parts.path)
        if parts.scheme != "https" or parts.netloc.lower() != "t.me" or not match:
            raise forms.ValidationError(
                "Нужна ссылка на публичную публикацию Telegram вида "
                "https://t.me/channel/123. Ссылка на канал без номера публикации не подходит."
            )
        username, post_id = match.groups()
        if int(post_id) > 9223372036854775807:
            raise forms.ValidationError("Номер публикации в ссылке слишком большой.")
        return f"https://t.me/{username.lower()}/{post_id}"
