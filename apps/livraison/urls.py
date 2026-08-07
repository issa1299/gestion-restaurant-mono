from django.urls import path

from . import views

app_name = "livraison"

urlpatterns = [
    path("", views.index, name="liste"),
    path("creer/<int:commande_id>/", views.creer_livraison, name="creer"),
    path("suivi/<int:commande_id>/<str:token>/", views.suivi_commande, name="suivi"),
    path("api/position/<int:commande_id>/<str:token>/", views.api_position, name="api_position"),
    path("<int:pk>/position/", views.maj_position, name="maj_position"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/modifier/", views.modifier, name="modifier"),
    path("<int:pk>/supprimer/", views.supprimer, name="supprimer"),
    path("<int:pk>/statut/", views.changer_statut, name="changer_statut"),
]
