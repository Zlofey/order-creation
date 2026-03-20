from django.db import models


class CreatedAtModel(models.Model):
    created_at = models.DateTimeField("created_at", auto_now_add=True, blank=True)

    class Meta:
        abstract = True
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class UpdatedAtModel(models.Model):
    updated_at = models.DateTimeField("updated_at", auto_now=True, blank=True)

    class Meta:
        abstract = True


class TimestampModel(CreatedAtModel, UpdatedAtModel):
    """Миксин, добавляющий поля created_at и updated_at."""

    class Meta:
        abstract = True
