from django.contrib import admin
from django.conf import settings
from django.contrib.auth import views as auth
from django.urls import path, re_path
from django.views.generic import RedirectView
from suppliers import views

urlpatterns = [
    path('admin', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin/', admin.site.urls),
    path('fornecedores/entrar/', views.SupplierLogin.as_view(), name='login'),
    path('fornecedores/sair/', auth.LogoutView.as_view(), name='logout'),
    path('fornecedores/senha/', views.SupplierPasswordChange.as_view(), name='password_change'),
    path('fornecedores/nova-senha/', views.ForcedPasswordChange.as_view(), name='force_password_change'),
    path('fornecedores/recuperar-senha/', auth.PasswordResetView.as_view(
        form_class=views.CNPJPasswordResetForm,
        template_name='form.html', email_template_name='password_reset_email.txt',
        subject_template_name='password_reset_subject.txt',
        success_url='/fornecedores/recuperar-senha/enviado/',
        extra_context={'title': 'Recuperar senha'}), name='password_reset'),
    path('fornecedores/recuperar-senha/enviado/', auth.PasswordResetDoneView.as_view(
        template_name='password_reset_message.html', extra_context={
            'title': 'Solicitação recebida',
            'email_enabled': settings.PASSWORD_RECOVERY_EMAIL_ENABLED,
        }), name='password_reset_done'),
    path('fornecedores/recuperar-senha/<uidb64>/<token>/', views.SupplierPasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('fornecedores/recuperar-senha/concluido/', auth.PasswordResetCompleteView.as_view(
        template_name='password_reset_message.html', extra_context={'title': 'Senha alterada', 'complete': True}), name='password_reset_complete'),
    path('fornecedores/importar/', views.import_csv, name='import_csv'),
    path('fornecedores/', views.dashboard, name='dashboard'),
    path('mirror-assets/<str:filename>', views.mirror_asset),
    re_path(r'^(?P<page>.*)$', views.public_page),
]
