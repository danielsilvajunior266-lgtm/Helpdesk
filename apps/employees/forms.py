from django import forms
from django.utils import timezone
from apps.employees.models import RegisteredEmployee, SalaryPayment, DailyHelper, DailyWork

class RegisteredEmployeeForm(forms.ModelForm):
    class Meta:
        model = RegisteredEmployee
        fields = ['name', 'role_title', 'cpf', 'phone', 'monthly_salary', 'payment_day', 'hire_date', 'pix_key', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': 'Ex: Marcos Vinícius Souza',
                'required': True,
            }),
            'role_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': 'Ex: Detalhador Master / Lavador Chefe',
                'required': True,
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': '000.000.000-00',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': '(11) 98888-7777',
            }),
            'monthly_salary': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': '2500.00',
                'step': '0.01',
                'required': True,
            }),
            'payment_day': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'min': '1',
                'max': '31',
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'type': 'date',
            }),
            'pix_key': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': 'CPF, E-mail, Celular ou Chave Aleatória',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-slate-700 text-[#1EA8D7] focus:ring-[#1EA8D7] bg-slate-800',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'rows': 2,
                'placeholder': 'Observações adicionais...',
            }),
        }


def get_previous_ref_month():
    today = timezone.now().date()
    if today.month == 1:
        return f"12/{today.year - 1}"
    return f"{today.month - 1:02d}/{today.year}"


class SalaryPaymentForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('cash', 'Dinheiro em Espécie'),
        ('bank_transfer', 'Transferência Bancária'),
        ('other', 'Outro'),
    ]

    reference_month = forms.CharField(
        label='Mês de Referência',
        initial=get_previous_ref_month,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
            'placeholder': 'Ex: 08/2026',
        })
    )
    base_salary = forms.DecimalField(
        label='Salário Base (R$)',
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
            'step': '0.01',
        })
    )
    bonus = forms.DecimalField(
        label='Bônus / Horas Extras / Adicionais (R$)',
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
            'step': '0.01',
        })
    )
    deductions = forms.DecimalField(
        label='Descontos / Vales / Adiantamentos (R$)',
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
            'step': '0.01',
        })
    )
    payment_date = forms.DateField(
        label='Data do Pagamento',
        initial=lambda: timezone.now().date().strftime('%Y-%m-%d'),
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'type': 'date',
            }
        )
    )
    payment_method = forms.ChoiceField(
        label='Forma de Pagamento',
        choices=PAYMENT_METHOD_CHOICES,
        initial='pix',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
        })
    )
    notes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
            'rows': 2,
            'placeholder': 'Observações do pagamento...',
        })
    )


class DailyHelperForm(forms.ModelForm):
    class Meta:
        model = DailyHelper
        fields = ['name', 'phone', 'pix_key', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': 'Ex: Roberto Carlos',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': '(11) 97777-6666',
            }),
            'pix_key': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': 'Chave PIX para pagamento da diária',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'rows': 2,
                'placeholder': 'Ex: Especialista em polimento e lavagem técnica...',
            }),
        }


class DailyWorkForm(forms.ModelForm):
    mark_as_paid = forms.BooleanField(
        label='Já efetuar pagamento e registrar saída no Livro Caixa',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 rounded border-slate-700 text-[#1EA8D7] focus:ring-[#1EA8D7] bg-slate-800',
        })
    )

    class Meta:
        model = DailyWork
        fields = ['helper', 'work_date', 'shift', 'daily_rate', 'activity_description', 'payment_method', 'notes']
        widgets = {
            'helper': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'required': True,
            }),
            'work_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'type': 'date',
            }),
            'shift': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
            }),
            'daily_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': '120.00',
                'step': '0.01',
                'required': True,
            }),
            'activity_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'placeholder': 'Ex: Lavagem externa e secagem de carros',
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1EA8D7]',
                'rows': 2,
                'placeholder': 'Observações...',
            }),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['helper'].queryset = DailyHelper.objects.filter(company=company)
        self.fields['work_date'].initial = timezone.now().date()
