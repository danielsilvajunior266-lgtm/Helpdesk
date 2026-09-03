from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.accounts.models import User

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
            'placeholder': 'seu@email.com',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
            'placeholder': '••••••••',
        })
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white'}),
        }
