from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserPreferences


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Crea preferencias automáticamente al crear un usuario"""
    if created:
        UserPreferences.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_preferences(sender, instance, **kwargs):
    """Guarda las preferencias cuando se guarda el usuario"""
    if hasattr(instance, 'preferences'):
        instance.preferences.save()