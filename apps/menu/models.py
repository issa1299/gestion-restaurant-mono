from django.db import models


class ProduitQuerySet(models.QuerySet):
    def disponibles(self):
        """Produits visibles au menu / POS : uniquement marqués disponibles.
        (Le suivi de stock est désactivé : les quantités sont ignorées.)"""
        return self.filter(disponible=True)


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.nom


class Produit(models.Model):
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.CASCADE,
        related_name="produits"
    )

    nom = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to="produits/",
        blank=True,
        null=True
    )

    disponible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProduitQuerySet.as_manager()

    class Meta:
        ordering = ["nom"]
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return self.nom