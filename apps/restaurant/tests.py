from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.restaurant.models import Temoignage
from apps.menu.models import Categorie, Produit
from apps.clients.models import Client as ClientModele
from apps.commandes.models import Commande, LigneCommande

User = get_user_model()


class TemoignageCRUDTests(TestCase):
    """CRUD complet des témoignages côté admin."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_t", email="adm_t@test.com", password="Test12345", role="ADMIN",
        )
        self.serveur = User.objects.create_user(
            username="ser_t", email="ser_t@test.com", password="Test12345", role="SERVEUR",
        )
        self.temoignage = Temoignage.objects.create(
            nom="Awa", note=5, message="Excellent restaurant !",
        )

    def test_gestion_accessible_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/temoignages/gestion/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Awa")

    def test_gestion_interdite_serveur(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/temoignages/gestion/")
        self.assertEqual(resp.status_code, 302)

    def test_ajouter_temoignage_admin(self):
        """Admin/Gérant gèrent les témoignages : ils peuvent en créer."""
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/ajouter/", {
            "nom": "Moussa",
            "note": "4",
            "message": "Très bon service",
            "actif": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Temoignage.objects.filter(nom="Moussa").exists())

    def test_modifier_temoignage_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/%d/modifier/" % self.temoignage.id, {
            "nom": "Awa D.",
            "note": "3",
            "message": "Bien",
            "actif": "",
        })
        self.assertEqual(resp.status_code, 302)
        self.temoignage.refresh_from_db()
        self.assertEqual(self.temoignage.nom, "Awa D.")

    def test_supprimer_temoignage_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/%d/supprimer/" % self.temoignage.id)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Temoignage.objects.filter(id=self.temoignage.id).exists())

    def test_toggle_actif_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/%d/toggle/" % self.temoignage.id)
        self.assertEqual(resp.status_code, 302)
        self.temoignage.refresh_from_db()
        self.assertFalse(self.temoignage.actif)

    def test_ajout_temoignage_interdit_serveur(self):
        """Les rôles non-direction ne peuvent pas créer de témoignage."""
        c = Client()
        c.force_login(self.serveur)
        resp = c.post("/temoignages/ajouter/", {
            "nom": "Intrus",
            "note": "4",
            "message": "Tentative",
            "actif": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Temoignage.objects.filter(nom="Intrus").exists())

    def test_page_publique_cache_inactifs(self):
        Temoignage.objects.create(nom="Caché", note=1, message="x", actif=False)
        resp = self.client.get("/temoignages/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Awa")
        self.assertNotContains(resp, "Caché")


class ConfirmationCommandeTokenTests(TestCase):
    """La page de confirmation est protégée par le token secret de la commande."""

    def setUp(self):
        self.categorie = Categorie.objects.create(nom="Plats")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Poulet", prix=2500,
        )
        self.client_modele = ClientModele.objects.create(nom="Awa", telephone="223")
        self.commande = Commande.objects.create(
            client=self.client_modele,
            type=Commande.LIVRAISON,
            statut=Commande.EN_ATTENTE,
            adresse_livraison="Bamako",
            telephone_livraison="223",
        )
        LigneCommande.objects.create(
            commande=self.commande, produit=self.produit, quantite=1, prix=2500,
        )

    def test_confirmation_avec_token(self):
        c = Client()
        resp = c.get("/commander/confirmation/%d/%s/" % (self.commande.id, self.commande.token))
        self.assertEqual(resp.status_code, 200)

    def test_confirmation_token_invalide_404(self):
        c = Client()
        resp = c.get("/commander/confirmation/%d/mauvais-token/" % self.commande.id)
        self.assertEqual(resp.status_code, 404)
