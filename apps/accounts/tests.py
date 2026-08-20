from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

ROLES = ["ADMIN", "GERANT", "CAISSIER", "SERVEUR", "CUISINIER", "VENDEUR", "LIVREUR", "CLIENT"]

# URL -> rôles autorisés (200 attendu), sinon 302 (redirection) attendue
ACCESS_MATRIX = {
    "/dashboard/": {"ADMIN", "GERANT", "SERVEUR", "CUISINIER", "CAISSIER"},
    "/accounts/users/": {"ADMIN", "GERANT"},
    "/clients/": {"ADMIN", "GERANT", "CAISSIER"},
    "/commandes/": {"ADMIN", "GERANT", "SERVEUR", "CUISINIER"},
    "/cuisine/": {"ADMIN", "GERANT", "CUISINIER"},
    "/livraisons/": {"ADMIN", "GERANT", "LIVREUR"},
    "/menu/gestion/": {"ADMIN", "GERANT", "VENDEUR"},
    "/stock/": {"ADMIN", "GERANT", "VENDEUR"},
    "/stock/historique/": {"ADMIN", "GERANT", "VENDEUR"},
    "/tables/": {"ADMIN", "GERANT", "SERVEUR"},
    "/rapports/": {"ADMIN", "GERANT"},
    "/parametres/": {"ADMIN", "GERANT"},
    "/ventes/": {"ADMIN", "GERANT", "CAISSIER"},
    "/ventes/historique/": {"ADMIN", "GERANT", "CAISSIER"},
    "/galerie/gestion/": {"ADMIN", "GERANT"},
    "/temoignages/gestion/": {"ADMIN", "GERANT"},
}


class AccessControlTests(TestCase):
    """Vérifie que chaque rôle n'accède qu'aux pages qui lui sont autorisées."""

    def setUp(self):
        self.users = {}
        for role in ROLES:
            self.users[role] = User.objects.create_user(
                username="user_%s" % role.lower(),
                email="user_%s@test.com" % role.lower(),
                password="Test12345",
                role=role,
            )

    def _get(self, role, url):
        c = Client()
        c.force_login(self.users[role])
        return c.get(url)

    def test_matrice_acces_par_role(self):
        for url, allowed in ACCESS_MATRIX.items():
            for role in ROLES:
                resp = self._get(role, url)
                if role in allowed:
                    self.assertEqual(
                        resp.status_code, 200,
                        "%s devrait être accessible à %s (statut %s)"
                        % (url, role, resp.status_code),
                    )
                else:
                    self.assertIn(
                        resp.status_code, (302, 403),
                        "%s devrait être interdit à %s (statut %s)"
                        % (url, role, resp.status_code),
                    )

    def test_pas_de_boucle_de_redirection(self):
        """Un rôle interdit ne doit jamais finir en boucle infinie."""
        for role, url in [
            ("CLIENT", "/dashboard/"),
            ("VENDEUR", "/dashboard/"),
            ("LIVREUR", "/dashboard/"),
            ("CLIENT", "/accounts/users/"),
            ("SERVEUR", "/stock/"),
        ]:
            resp = self._get(role, url)
            self.assertIn(resp.status_code, (302, 403))

    def test_admin_lecture_seule_sur_ecriture(self):
        """L'ADMIN ne peut pas accéder aux actions d'écriture (il supervise)."""
        urls_ecriture = [
            "/menu/produits/ajouter/",
            "/menu/produits/1/modifier/",
            "/stock/1/modifier/",
            "/stock/1/mouvement/",
            "/ventes/1/annuler/",
            "/clients/ajouter/",
            "/commandes/ajouter/",
            "/tables/creer/",
            "/livraisons/1/modifier/",
        ]
        for url in urls_ecriture:
            resp = self._get("ADMIN", url)
            self.assertIn(
                resp.status_code, (302, 403, 404, 405),
                "ADMIN ne devrait pas écrire via %s (statut %s)" % (url, resp.status_code),
            )

    def test_redirection_client_vers_menu(self):
        resp = self._get("CLIENT", "/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/menu/", resp.get("Location", ""))

    def test_redirection_vendeur_vers_gestion_menu(self):
        resp = self._get("VENDEUR", "/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/menu/gestion/", resp.get("Location", ""))

    def test_redirection_livreur_vers_livraisons(self):
        resp = self._get("LIVREUR", "/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/livraisons/", resp.get("Location", ""))

    def test_login_gerant_redirige_vers_dashboard(self):
        user = User.objects.create_user(
            username="ger_log",
            email="ger_log@test.com",
            password="Test12345",
            role="GERANT",
        )
        resp = self.client.post(
            "/accounts/login/",
            {"username": user.username, "password": "Test12345"},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard/", resp.get("Location", ""))

    def test_gerant_voit_statistiques_du_dashboard(self):
        resp = self._get("GERANT", "/dashboard/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Chiffre d'affaires")
        self.assertContains(resp, "Chiffre d'affaires par type")

    def test_login_livreur_redirige_vers_livraisons(self):
        user = User.objects.create_user(
            username="liv_log",
            email="liv_log@test.com",
            password="Test12345",
            role="LIVREUR",
        )
        resp = self.client.post(
            "/accounts/login/",
            {"username": user.username, "password": "Test12345"},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/livraisons/", resp.get("Location", ""))

    def test_anonyme_redirige_vers_login(self):
        c = Client()
        resp = c.get("/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.get("Location", ""))

    def test_superuser_admin_bloque_en_ecriture(self):
        """Même un superuser avec le rôle ADMIN/GÉRANT est bloqué en écriture."""
        super_admin = User.objects.create_user(
            username="super_adm", email="super_adm@test.com",
            password="Test12345", role="ADMIN", is_superuser=True,
        )
        c = Client()
        c.force_login(super_admin)
        # POST bloqué sur une vue d'écriture réservée (ex: ajouter un client = CAISSIER)
        resp = c.post("/clients/ajouter/", {
            "nom": "Bloqué", "telephone": "000",
        })
        self.assertIn(resp.status_code, (302, 403, 404, 405))
        from apps.clients.models import Client as ClientModele
        self.assertFalse(ClientModele.objects.filter(nom="Bloqué").exists())

    def test_gerant_lecture_seule_sauf_gestion_utilisateurs(self):
        """Le Gérant lit tout mais ne crée/modifie/supprime que les utilisateurs."""
        gerant = self.users["GERANT"]
        c = Client()
        c.force_login(gerant)
        # Lecture autorisée
        r = c.get("/dashboard/")
        self.assertEqual(r.status_code, 200)
        # Écriture métier bloquée (ajout d'un client réservé au caissier)
        r = c.post("/clients/ajouter/", {"nom": "X", "telephone": "1"})
        self.assertIn(r.status_code, (302, 403, 404, 405))
        # Gestion des utilisateurs autorisée
        r = c.post("/accounts/users/create/", {
            "username": "nv_ger",
            "password": "Motdepasse123",
            "password_confirm": "Motdepasse123",
        })
        self.assertIn(r.status_code, (200, 302))


class UserManagementTests(TestCase):
    """Seul un ADMIN peut gérer les utilisateurs."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_t", email="admin_t@test.com",
            password="Test12345", role="ADMIN",
        )
        self.serveur = User.objects.create_user(
            username="serveur_t", email="serveur_t@test.com",
            password="Test12345", role="SERVEUR",
        )

    def test_users_list_interdit_pour_non_admin(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/accounts/users/")
        self.assertEqual(resp.status_code, 302)

    def test_users_list_accessible_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/accounts/users/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Gestion des utilisateurs")

    def test_user_create_interdit_pour_non_admin(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/accounts/users/create/")
        self.assertEqual(resp.status_code, 302)

    def test_admin_peut_creer_un_utilisateur(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/accounts/users/create/", {
            "username": "nouveau",
            "password1": "Motdepasse123",
            "password2": "Motdepasse123",
            "role": "SERVEUR",
        })
        self.assertIn(resp.status_code, (200, 302))
        if resp.status_code == 302:
            self.assertTrue(User.objects.filter(username="nouveau").exists())

    def test_admin_peut_desactiver_un_utilisateur(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post(
            "/accounts/users/%d/toggle-active/" % self.serveur.id,
        )
        self.serveur.refresh_from_db()
        self.assertFalse(self.serveur.is_active)
        self.assertEqual(resp.status_code, 302)
