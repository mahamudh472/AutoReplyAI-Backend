from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .services import create_default_organization_for_user

User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save_create_organization(sender, instance, created, **kwargs):
    """
    Automatically creates a default organization and owner membership when a user account
    is active (e.g. upon creation or after email verification activation).
    """
    if instance.is_active:
        create_default_organization_for_user(instance)
