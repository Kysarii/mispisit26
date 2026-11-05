from django.db import models


class Source(models.Model):
    title = models.CharField("Название канала", max_length=80)
    link = models.URLField("Ссылка на канал", max_length=300, unique=True)

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"

    def __str__(self):
        return self.title


class Publication(models.Model):
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, related_name="publications",
        verbose_name="Источник",
    )
    external_id = models.PositiveBigIntegerField("Номер публикации в Telegram")
    title = models.CharField("Заголовок", max_length=160)
    content_text = models.TextField("Текст новости")
    indexed_at = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"
        ordering = ["-indexed_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"], name="unique_source_external_id"
            ),
        ]

    @property
    def source_url(self):
        return f"{self.source.link}/{self.external_id}"

    def __str__(self):
        return self.title
