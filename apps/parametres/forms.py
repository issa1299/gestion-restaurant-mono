from django import forms
from .models import ParametreRestaurant

class ParametreForm(forms.ModelForm):
    class Meta:
        model = ParametreRestaurant
        fields = ['nom', 'adresse', 'telephone', 'email', 'logo', 'devise', 'message_ticket',
                  'jours_ouverture', 'ouverture_midi', 'fermeture_midi', 'ouverture_soir', 'fermeture_soir',
                  'smtp_host', 'smtp_port', 'smtp_utilisateur', 'smtp_mot_de_passe', 'smtp_use_tls', 'email_expediteur',
                  'url_site']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'adresse': forms.Textarea(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'rows': 2}),
            'telephone': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'devise': forms.Select(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none bg-white'}, choices=[
                ('FCFA', 'Franc CFA (FCFA)'),
            ]),
            'message_ticket': forms.Textarea(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'rows': 2}),
            'logo': forms.FileInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'jours_ouverture': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'placeholder': 'Ex : Lundi au Dimanche'}),
            'ouverture_midi': forms.TimeInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'type': 'time'}),
            'fermeture_midi': forms.TimeInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'type': 'time'}),
            'ouverture_soir': forms.TimeInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'type': 'time'}),
            'fermeture_soir': forms.TimeInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'type': 'time'}),
            'smtp_host': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'placeholder': 'Ex : smtp.gmail.com'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'smtp_utilisateur': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'placeholder': 'Ex : monrestaurant@gmail.com'}),
            'smtp_mot_de_passe': forms.PasswordInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'placeholder': 'Mot de passe / clé d\'application'}),
            'smtp_use_tls': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-gray-300 text-orange-500 focus:ring-orange-500'}),
            'email_expediteur': forms.EmailInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'placeholder': 'Ex : commandes@monrestaurant.com'}),
            'url_site': forms.URLInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'placeholder': 'Ex : https://issa72.pythonanywhere.com'}),
        }
