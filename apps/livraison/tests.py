import json

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.clients.models import Client as ClientModele
from apps.menu.models import Categorie, Produit
from apps.commandes.models import Commande, LigneCommande
from apps.livraison.models import Livraison

User = get_user_model()


class LivraisonCRUDTests(TestCase):
    """Détail, modification, suppression et assignation d'une livraison."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_l", email="adm_l@test.com", password="Test12345", role="ADMIN",
        )
        self.livreur = User.objects.create_user(
            username="liv_l", email="liv_l@test.com", password="Test12345", role="LIVREUR",
        )
        self.client_user = User.objects.create_user(
            username="cli_l", email="cli_l@test.com", password="Test12345", role="CLIENT",
        )

        self.categorie = Categorie.objects.create(nom="Boissons")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Jus", prix=500,
        )
        self.client = ClientModele.objects.create(nom="Awa", telephone="223")
        self.commande = Commande.objects.create(
            client=self.client, statut=Commande.PRETE, type=Commande.LIVRAISON,
        )
        LigneCommande.objects.create(
            commande=self.commande, produit=self.produit, quantite=2, prix=500,
        )
        self.livraison = Livraison.objects.create(
            commande=self.commande, adresse="Bamako", telephone="223",
        )

    def test_detail_livraison(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/livraisons/%d/" % self.livraison.id)
        self.assertEqual(resp.status_code, 200)

    def test_modifier_livraison(self):
        c = Client()
        c.force_login(self.livreur)
        resp = c.post("/livraisons/%d/modifier/" % self.livraison.id, {
            "adresse": "Bamako - ACI 2000",
            "telephone": "223 222222",
            "notes": "Appeler avant",
            "livreur": self.livreur.id,
        })
        self.assertEqual(resp.status_code, 302)
        self.livraison.refresh_from_db()
        self.assertEqual(self.livraison.adresse, "Bamako - ACI 2000")
        self.assertEqual(self.livraison.notes, "Appeler avant")
        self.assertEqual(self.livraison.livreur, self.livreur)

    def test_modification_interdite_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/livraisons/%d/modifier/" % self.livraison.id, {
            "adresse": "Bamako - ACI 2000",
            "telephone": "223 222222",
            "notes": "Appeler avant",
            "livreur": self.livreur.id,
        })
        self.assertEqual(resp.status_code, 302)
        self.livraison.refresh_from_db()
        self.assertEqual(self.livraison.adresse, "Bamako")

    def test_supprimer_livraison(self):
        c = Client()
        c.force_login(self.livreur)
        resp = c.post("/livraisons/%d/supprimer/" % self.livraison.id)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Livraison.objects.filter(id=self.livraison.id).exists())

    def test_detail_interdit_client(self):
        c = Client()
        c.force_login(self.client_user)
        resp = c.get("/livraisons/%d/" % self.livraison.id)
        self.assertEqual(resp.status_code, 302)

    def test_modifier_accessible_livreur(self):
        c = Client()
        c.force_login(self.livreur)
        resp = c.get("/livraisons/%d/modifier/" % self.livraison.id)
        self.assertEqual(resp.status_code, 200)

    def test_position_endpoint_updates_livraison(self):
        c = Client()
        c.force_login(self.livreur)
        resp = c.post(
            "/livraisons/%d/position/" % self.livraison.id,
            data=json.dumps({"latitude": 12.6392, "longitude": -8.0029}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.livraison.refresh_from_db()
        self.assertEqual(self.livraison.latitude, 12.6392)
        self.assertEqual(self.livraison.longitude, -8.0029)

    def test_tracking_page_is_available_for_customer(self):
        c = Client()
        resp = c.get("/livraisons/suivi/%d/%s/" % (self.commande.id, self.commande.token))
        self.assertEqual(resp.status_code, 200)


class TokenSecuriteTests(TestCase):
    """Le token secret protège les pages publiques de suivi."""

    def setUp(self):
        self.categorie = Categorie.objects.create(nom="Boissons")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Jus", prix=500,
        )
        self.client = ClientModele.objects.create(nom="Awa", telephone="223")
        self.commande = Commande.objects.create(
            client=self.client, statut=Commande.PRETE, type=Commande.LIVRAISON,
        )
        LigneCommande.objects.create(
            commande=self.commande, produit=self.produit, quantite=2, prix=500,
        )
        Livraison.objects.create(
            commande=self.commande, adresse="Bamako", telephone="223",
        )

    def test_token_auto_genere_et_unique(self):
        self.assertTrue(self.commande.token)
        autre = Commande.objects.create(
            client=self.client, statut=Commande.EN_ATTENTE, type=Commande.LIVRAISON,
        )
        self.assertNotEqual(self.commande.token, autre.token)

    def test_tracking_token_invalide_404(self):
        c = Client()
        resp = c.get("/livraisons/suivi/%d/mauvais-token/" % self.commande.id)
        self.assertEqual(resp.status_code, 404)

    def test_api_position_avec_token(self):
        c = Client()
        resp = c.get("/livraisons/api/position/%d/%s/" % (self.commande.id, self.commande.token))
        self.assertEqual(resp.status_code, 200)

    def test_api_position_token_invalide_404(self):
        c = Client()
        resp = c.get("/livraisons/api/position/%d/mauvais-token/" % self.commande.id)
        self.assertEqual(resp.status_code, 404)
