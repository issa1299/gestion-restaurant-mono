from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from apps.accounts.decorators import role_required
from apps.parametres.models import ParametreRestaurant
from .models import Table


@role_required(["ADMIN", "GERANT", "SERVEUR"])
def liste_tables(request):
    tables = Table.objects.all()
    total = tables.count()
    disponibles = tables.filter(disponible=True).count()
    occupees = tables.filter(disponible=False).count()

    return render(request, "tables/liste.html", {
        "tables": tables,
        "total": total,
        "disponibles": disponibles,
        "occupees": occupees,
        "url_site": ParametreRestaurant.load().url_site,
    })


@role_required(["SERVEUR"])
def creer_table(request):
    if request.method == "POST":
        numero = request.POST.get("numero")
        capacite = request.POST.get("capacite", 4)

        if Table.objects.filter(numero=numero).exists():
            messages.error(request, f"La table numéro {numero} existe déjà.")
            return redirect("tables:creer")

        Table.objects.create(numero=numero, capacite=capacite)
        messages.success(request, f"Table {numero} créée avec succès.")
        return redirect("tables:liste")

    return render(request, "tables/form.html", {"action": "Créer", "table": None})


@role_required(["SERVEUR"])
def modifier_table(request, id):
    table = get_object_or_404(Table, id=id)

    if request.method == "POST":
        table.numero = request.POST.get("numero")
        table.capacite = request.POST.get("capacite", 4)
        table.save()
        messages.success(request, f"Table {table.numero} modifiée.")
        return redirect("tables:liste")

    return render(request, "tables/form.html", {"action": "Modifier", "table": table})


@role_required(["SERVEUR"])
def supprimer_table(request, id):
    table = get_object_or_404(Table, id=id)

    if request.method == "POST":
        num = table.numero
        table.delete()
        messages.success(request, f"Table {num} supprimée.")
        return redirect("tables:liste")

    return render(request, "tables/supprimer.html", {"table": table})


@role_required(["SERVEUR"])
def toggle_table(request, id):
    table = get_object_or_404(Table, id=id)
    table.disponible = not table.disponible
    table.save()
    status = "disponible" if table.disponible else "occupée"
    messages.success(request, f"Table {table.numero} marquée comme {status}.")
    return redirect("tables:liste")


def _base_url(request=None):
    url_site = ParametreRestaurant.load().url_site
    if url_site:
        return url_site.rstrip("/")
    if request is not None:
        return f"{request.scheme}://{request.get_host()}"
    return "http://localhost:8080"


def _lien_qr_table(table, request=None):
    base = _base_url(request)
    return base + "/commandes/client/?table=" + str(table.numero)


def _generer_qr_png(lien):
    from PIL import Image, ImageDraw
    import qrcode
    qr = qrcode.QRCode(box_size=20, border=4)
    qr.add_data(lien)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    return img


@role_required(["ADMIN", "GERANT", "SERVEUR"])
def qr_codes(request):
    tables = Table.objects.all()
    liens = [(t, _lien_qr_table(t, request)) for t in tables]
    return render(request, "tables/qr_codes.html", {
        "tables": tables,
        "liens": liens,
    })


@role_required(["ADMIN", "GERANT", "SERVEUR"])
def telecharger_qr(request, id):
    table = get_object_or_404(Table, id=id)
    lien = _lien_qr_table(table, request)
    img = _generer_qr_png(lien)
    import io
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="table-{table.numero}-qr.png"'
    return response
