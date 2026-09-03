from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.forms import LoginForm, ProfileForm, CustomerRegistrationForm

def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'customer':
            return redirect('portal:select_company')
        return redirect('orders:kanban')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo de volta, {user.first_name or user.username}!')
            next_url = request.GET.get('next')
            if next_url and next_url != 'orders:kanban':
                return redirect(next_url)
            
            if user.role == 'customer':
                return redirect('portal:select_company')
            return redirect('orders:kanban')
        else:
            messages.error(request, 'E-mail ou senha incorretos. Verifique suas credenciais.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Sessão encerrada com sucesso.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


def register_customer_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'customer':
            return redirect('portal:select_company')
        return redirect('orders:kanban')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Conta criada com sucesso! Seja bem-vindo(a), {user.first_name}!')
            return redirect('portal:select_company')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo para concluir seu cadastro.')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})
