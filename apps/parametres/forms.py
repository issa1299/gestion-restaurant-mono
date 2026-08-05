from django import forms
from .models import ParametreRestaurant

class ParametreForm(forms.ModelForm):
    class Meta:
        model = ParametreRestaurant
        fields = ['nom', 'adresse', 'telephone', 'email', 'logo', 'devise', 'message_ticket',
                  'jours_ouverture', 'ouverture_midi', 'fermeture_midi', 'ouverture_soir', 'fermeture_soir']
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
        }
