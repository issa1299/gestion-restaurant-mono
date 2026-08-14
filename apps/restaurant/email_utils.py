from django.utils.html import escape
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives, get_connection
from apps.parametres.models import ParametreRestaurant

from .models import Reservation


def _enveloppe_html(logo_html, contenu_html, parametres, annee):
    footer = ""
    if parametres.adresse or parametres.telephone:
        extra = ""
        if parametres.telephone:
            extra = f"<br>Tél : {escape(parametres.telephone)}"
        footer = f"<tr><td style='padding:0 32px 16px 32px;font-size:12px;color:#94a3b8;line-height:1.5;'>{escape(parametres.adresse or '')}{extra}</td></tr>"
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background-color:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:24px 0;">
        <tr>
          <td align="center">
            <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#f97316,#ea580c);padding:28px 32px;text-align:center;">
                  {logo_html}
                </td>
              </tr>
              {contenu_html}
              {footer}
              <tr>
                <td style="padding:20px 32px;text-align:center;border-top:1px solid #f1f5f9;">
                  <p style="margin:0;font-size:12px;color:#94a3b8;">© {annee} {escape(parametres.nom)} — Merci de votre confiance</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def charger_logo(parametres):
    """Retourne (logo_html, logo_bytes). Toujours le nom du restaurant (sans image)."""
    return (
        "<h1 style='margin:0;font-size:26px;color:#ffffff;letter-spacing:1px;'>"
        + escape(parametres.nom)
        + "</h1>",
        None,
    )


def envoyer_email(sujet, corps_texte, destinataire, corps_html, parametres=None, logo_bytes=None):
    """Envoie un email via la config SMTP des paramètres (console si absente).
    Retourne (ok, message_erreur)."""
    parametres = parametres or ParametreRestaurant.load()
    expediteur = parametres.email_expediteur or parametres.email

    try:
        if parametres.smtp_host and expediteur:
            backend = "django.core.mail.backends.smtp.EmailBackend"
            kwargs = {
                "host": parametres.smtp_host,
                "port": parametres.smtp_port,
                "username": parametres.smtp_utilisateur,
                "password": parametres.smtp_mot_de_passe,
                "use_tls": parametres.smtp_use_tls,
            }
        else:
            backend = "django.core.mail.backends.console.EmailBackend"
            kwargs = {}
        connection = get_connection(backend, fail_silently=False, **kwargs)
        email_msg = EmailMultiAlternatives(
            sujet,
            corps_texte,
            expediteur or "noreply@restaurantpro.local",
            [destinataire],
            connection=connection,
        )
        if logo_bytes:
            email_msg.attach("logo_restaurant", logo_bytes, "image/jpeg")
        email_msg.attach_alternative(corps_html, "text/html")
        email_msg.send()
        return True, None
    except Exception as e:
        return False, str(e)


def envoyer_reponse_message(message_contact, reponse):
    """Email de réponse à un message de contact. Retourne (ok, erreur)."""
    parametres = ParametreRestaurant.load()
    logo_html, logo_bytes = charger_logo(parametres)
    reponse_texte = escape(reponse)
    corps_texte = (
        f"Bonjour {message_contact.nom},\n\n"
        f"{reponse}\n\n"
        f"Cordialement,\n{parametres.nom}"
    )
    contenu = f"""
    <tr>
      <td style="padding:36px 32px 24px 32px;">
        <p style="margin:0 0 16px 0;font-size:16px;color:#334155;line-height:1.6;">Bonjour <strong style="color:#0f172a;">{escape(message_contact.nom)}</strong>,</p>
        <p style="margin:0 0 24px 0;font-size:15px;color:#475569;line-height:1.7;">{reponse_texte}</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#fff7ed;border:1px solid #fed7aa;border-radius:12px;margin:0 0 24px 0;">
          <tr>
            <td style="padding:16px 20px;font-size:13px;color:#9a3412;line-height:1.6;">
              <strong style="color:#c2410c;">Message d'origine :</strong><br>
              Sujet : {escape(message_contact.sujet or 'Sans objet')}<br>
              {escape(message_contact.message)}
            </td>
          </tr>
        </table>
        <p style="margin:0;font-size:14px;color:#334155;line-height:1.6;">Cordialement,<br><strong style="color:#0f172a;">{escape(parametres.nom)}</strong></p>
      </td>
    </tr>
    """
    sujet = f"RE: {message_contact.sujet or 'Votre message'} - {parametres.nom}"
    corps_html = _enveloppe_html(logo_html, contenu, parametres, timezone.now().year)
    return envoyer_email(sujet, corps_texte, message_contact.email, corps_html, parametres, logo_bytes)


def envoyer_confirmation_reservation(reservation):
    """Email de confirmation (ou annulation) de réservation. Retourne (ok, erreur)."""
    parametres = ParametreRestaurant.load()
    logo_html, logo_bytes = charger_logo(parametres)
    libelle = dict(Reservation.STATUTS).get(reservation.statut, reservation.statut)
    confirme = reservation.statut == "CONFIRMEE"

    if confirme:
        badge = "<span style='display:inline-block;background:#dcfce7;color:#15803d;font-weight:700;padding:6px 14px;border-radius:999px;font-size:13px;'>Réservation confirmée</span>"
        intro = "Votre réservation a été confirmée avec succès."
    else:
        badge = "<span style='display:inline-block;background:#fee2e2;color:#b91c1c;font-weight:700;padding:6px 14px;border-radius:999px;font-size:13px;'>Réservation annulée</span>"
        intro = "Votre réservation a été annulée."

    corps_texte = (
        f"Bonjour {reservation.nom},\n\n"
        f"{intro}\n\n"
        f"Date : {reservation.date}\n"
        f"Heure : {reservation.heure}\n"
        f"Personnes : {reservation.nombre_personnes}\n"
        f"Statut : {libelle}\n\n"
        f"Cordialement,\n{parametres.nom}"
    )
    date_fr = reservation.date.strftime("%d/%m/%Y")
    heure_fr = reservation.heure.strftime("%H:%M")
    telephone = reservation.telephone or ""
    contact_email = parametres.email or parametres.email_expediteur
    contenu = f"""
    <tr>
      <td style="padding:36px 32px 24px 32px;">
        <p style="margin:0 0 16px 0;font-size:16px;color:#334155;line-height:1.6;">Bonjour <strong style="color:#0f172a;">{escape(reservation.nom)}</strong>,</p>
        <p style="margin:0 0 20px 0;font-size:15px;color:#475569;line-height:1.7;">{intro}</p>
        <div style="text-align:center;margin:0 0 24px 0;">{badge}</div>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;margin:0 0 24px 0;">
          <tr>
            <td style="padding:18px 20px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding:4px 0;font-size:13px;color:#64748b;">Date</td>
                  <td style="padding:4px 0;font-size:14px;color:#0f172a;font-weight:600;text-align:right;">{date_fr}</td>
                </tr>
                <tr>
                  <td style="padding:4px 0;font-size:13px;color:#64748b;">Heure</td>
                  <td style="padding:4px 0;font-size:14px;color:#0f172a;font-weight:600;text-align:right;">{heure_fr}</td>
                </tr>
                <tr>
                  <td style="padding:4px 0;font-size:13px;color:#64748b;">Personnes</td>
                  <td style="padding:4px 0;font-size:14px;color:#0f172a;font-weight:600;text-align:right;">{reservation.nombre_personnes}</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        {f"<p style='margin:0 0 8px 0;font-size:14px;color:#334155;'>Message : {escape(reservation.message)}</p>" if reservation.message else ""}
        <p style="margin:0;font-size:14px;color:#334155;line-height:1.6;">Cordialement,<br><strong style="color:#0f172a;">{escape(parametres.nom)}</strong></p>
        {f"<p style='margin:12px 0 0 0;font-size:12px;color:#94a3b8;'>Pour toute question, contactez-nous{f' au {escape(telephone)}' if telephone else ''}{f' ou par email à {escape(contact_email)}' if contact_email else ''}.</p>" if (telephone or contact_email) else ""}
      </td>
    </tr>
    """
    sujet = f"{'Confirmation' if confirme else 'Annulation'} de réservation - {parametres.nom}"
    corps_html = _enveloppe_html(logo_html, contenu, parametres, timezone.now().year)
    if not reservation.email:
        return False, "Aucun email renseigné sur cette réservation."
    return envoyer_email(sujet, corps_texte, reservation.email, corps_html, parametres, logo_bytes)