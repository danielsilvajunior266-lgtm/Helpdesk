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


class CustomerRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label='Nome Completo',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7] focus:border-transparent transition-all',
            'placeholder': 'Seu Nome Completo',
            'autofocus': True,
        })
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7] focus:border-transparent transition-all',
            'placeholder': 'seu.email@exemplo.com',
        })
    )
    phone = forms.CharField(
        label='Telefone / WhatsApp',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7] focus:border-transparent transition-all',
            'placeholder': '(11) 99999-9999',
        })
    )
    password = forms.CharField(
        label='Senha de Acesso',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7] focus:border-transparent transition-all',
            'placeholder': 'Mínimo 6 caracteres',
        })
    )
    confirm_password = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7] focus:border-transparent transition-all',
            'placeholder': 'Repita sua senha',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado no sistema.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and len(password) < 6:
            self.add_error('password', 'A senha deve conter pelo menos 6 caracteres.')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'As senhas informadas não coincidem.')

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        full_name = cleaned_data['full_name'].strip()
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        user = User.objects.create_user(
            email=cleaned_data['email'],
            password=cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
            phone=cleaned_data.get('phone', ''),
            role='customer'
        )
        return user
