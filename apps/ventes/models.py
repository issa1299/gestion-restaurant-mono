from django.db import models
from apps.accounts.models import CustomUser
from apps.menu.models import Produit
from apps.tables.models import Table


class Vente(models.Model):

    MODE_PAIEMENT = (

        ("ESPECES", "Espèces"),
        ("ORANGE", "Orange Money"),
        ("WAVE", "Wave"),
        ("CARTE", "Carte bancaire"),

    )

    TYPE_COMMANDE = (
        ("SUR_PLACE", "Sur place"),
        ("A_EMPORTER", "À emporter"),
        ("LIVRAISON", "Livraison"),
    )

    caissier = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ventes"
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventes",
        verbose_name="Table"
    )

    type_commande = models.CharField(
        max_length=20,
        choices=TYPE_COMMANDE,
        default="SUR_PLACE",
        verbose_name="Type de commande"
    )

    remise_pourcent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Remise (%)"
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    montant_recu = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant reçu"
    )

    monnaie_rendue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monnaie rendue"
    )

    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )

    annulee = models.BooleanField(
        default=False,
        verbose_name="Vente annulée"
    )

    annule_le = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Annulée le"
    )

    annule_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventes_annulees"
    )

    class Meta:

        ordering = ["-created_at"]


    def __str__(self):

        return f"Vente N° {self.id}"

    @property
    def sous_total_brut(self):
        return sum(detail.sous_total for detail in self.details.all())

    @property
    def remise_montant(self):
        brut = self.sous_total_brut
        return brut * (self.remise_pourcent or 0) / 100




class DetailVente(models.Model):


    vente = models.ForeignKey(
        Vente,
        on_delete=models.CASCADE,
        related_name="details"
    )


    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE
    )


    quantite = models.PositiveIntegerField()


    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    sous_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    def __str__(self):

        return self.produit.nom