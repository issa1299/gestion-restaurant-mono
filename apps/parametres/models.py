from django.db import models
from django.core.cache import cache


class ParametreRestaurant(models.Model):
    nom = models.CharField(max_length=100, default="RestaurantPro")
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    logo = models.ImageField(upload_to="parametres/", blank=True, null=True)
    
    devise = models.CharField(max_length=10, default="FCFA")
    
    message_ticket = models.TextField(blank=True, default="Merci de votre visite et à bientôt !")

    # Impression automatique silencieuse du ticket (PC caisse)
    impression_silencieuse = models.BooleanField(default=False)

    # Horaires d'ouverture (deux services : midi et soir)
    jours_ouverture = models.CharField(
        max_length=50, blank=True, default="Lundi au Dimanche"
    )
    ouverture_midi = models.TimeField(null=True, blank=True)
    fermeture_midi = models.TimeField(null=True, blank=True)
    ouverture_soir = models.TimeField(null=True, blank=True)
    fermeture_soir = models.TimeField(null=True, blank=True)

    # E-mails aux clients (SMTP)
    smtp_host = models.CharField(max_length=150, blank=True, default="")
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_utilisateur = models.CharField(max_length=150, blank=True, default="")
    smtp_mot_de_passe = models.CharField(max_length=200, blank=True, default="")
    smtp_use_tls = models.BooleanField(default=True)
    email_expediteur = models.EmailField(blank=True, default="")

    # Site & QR codes des tables
    url_site = models.URLField(blank=True, default="")

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule instance
        self.pk = 1
        super(ParametreRestaurant, self).save(*args, **kwargs)
        cache.delete("parametres_restaurant")

    @classmethod
    def load(cls):
        obj = cache.get("parametres_restaurant")
        if obj is None:
            obj, created = cls.objects.get_or_create(pk=1)
            cache.set("parametres_restaurant", obj, 300)
        return obj

    def __str__(self):
        return "Paramètres du Restaurant"
