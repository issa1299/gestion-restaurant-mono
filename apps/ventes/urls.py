from django.urls import path
from . import views


app_name = "ventes"


urlpatterns = [

    path(
        "",
        views.pos,
        name="pos"
    ),
    path(
        "enregistrer/",
        views.enregistrer_vente,
        name="enregistrer_vente"
    ),
    path(
        "commandes/creer/",
        views.creer_commande,
        name="creer_commande"
    ),
    path(
        "commandes/encaisser/",
        views.encaisser_commande,
        name="encaisser_commande"
    ),


    path(
        "historique/",
        views.historique,
        name="historique"
    ),

    path(
        "<int:vente_id>/",
        views.detail_vente,
        name="detail"
    ),

    path(
        "<int:vente_id>/annuler/",
        views.annuler_vente,
        name="annuler"
    ),


    path(
        "ticket/<int:vente_id>/",
        views.ticket,
        name="ticket"
    ),

]
