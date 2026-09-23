# Ticket 58mm (XPrinter) — largeur du papier thermique
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parametres', '0007_parametrerestaurant_tiktok'),
    ]

    operations = [
        migrations.AddField(
            model_name='parametrerestaurant',
            name='largeur_ticket',
            field=models.CharField(choices=[('58', '58 mm (XPrinter 58mm)'), ('80', '80 mm')], default='58', max_length=5),
        ),
    ]
