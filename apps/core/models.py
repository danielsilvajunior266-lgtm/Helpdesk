from django.db import models

class TimeStampedModel(models.Model):
    """
    Modelo base abstrato que fornece campos timestamp criados e atualizados automaticamente.
    """
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        abstract = True
