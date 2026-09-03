from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    """
    Gerenciador customizado que utiliza o e-mail como identificador único para autenticação.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O endereço de e-mail é obrigatório.')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email.split('@')[0])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrador (Dono do SaaS)'),
        ('owner', 'Proprietário / Gerente do Lava-Jato'),
        ('employee', 'Lavador / Operador de Pátio'),
        ('customer', 'Cliente Motorista (App Mobile)'),
    ]

    email = models.EmailField('E-mail', unique=True)
    phone = models.CharField('Telefone / Celular', max_length=20, blank=True)
    role = models.CharField('Perfil de Acesso', max_length=20, choices=ROLE_CHOICES, default='employee')
    company = models.ForeignKey(
        'saas_core.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Empresa'
    )
    avatar = models.ImageField('Foto de Perfil', upload_to='avatars/', blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['first_name', 'last_name', 'email']

    def __str__(self):
        name = self.get_full_name() or self.username
        return f"{name} ({self.get_role_display()})"

    @property
    def is_owner(self):
        return self.role in ['owner', 'superadmin']

    @property
    def is_operator(self):
        return self.role in ['employee', 'owner', 'superadmin']

    @property
    def is_customer(self):
        return self.role == 'customer'
