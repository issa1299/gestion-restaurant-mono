from django.urls import path
from . import views

app_name = "tables"

urlpatterns = [
    path("", views.liste_tables, name="liste"),
    path("creer/", views.creer_table, name="creer"),
    path("<int:id>/modifier/", views.modifier_table, name="modifier"),
    path("<int:id>/supprimer/", views.supprimer_table, name="supprimer"),
    path("<int:id>/toggle/", views.toggle_table, name="toggle"),
    path("qr-codes/", views.qr_codes, name="qr_codes"),
    path("<int:id>/qr/telecharger/", views.telecharger_qr, name="telecharger_qr"),
]
