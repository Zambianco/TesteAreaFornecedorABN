import json
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from .forms import CNPJLoginForm, CNPJPasswordResetForm, UploadForm
from .importer import import_evaluations
from .models import Evaluation


class SupplierLogin(LoginView):
    template_name = 'form.html'
    authentication_form = CNPJLoginForm
    extra_context = {'title': 'Área do fornecedor'}


class SupplierPasswordChange(PasswordChangeView):
    template_name = 'form.html'
    success_url = '/fornecedores/'
    extra_context = {'title': 'Alterar senha'}

    def form_valid(self, form):
        response = super().form_valid(form)
        supplier = getattr(self.request.user, 'supplier', None)
        if supplier and supplier.must_change_password:
            supplier.must_change_password = False
            supplier.save(update_fields=['must_change_password'])
        return response


class ForcedPasswordChange(SupplierPasswordChange):
    template_name = 'force_password_change.html'
    extra_context = {'title': 'Crie uma nova senha'}

    def dispatch(self, request, *args, **kwargs):
        supplier = getattr(request.user, 'supplier', None) if request.user.is_authenticated else None
        if request.user.is_authenticated and supplier and not supplier.must_change_password:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class SupplierPasswordResetConfirm(PasswordResetConfirmView):
    template_name = 'form.html'
    success_url = '/fornecedores/recuperar-senha/concluido/'
    extra_context = {'title': 'Definir nova senha'}

    def form_valid(self, form):
        response = super().form_valid(form)
        supplier = getattr(self.user, 'supplier', None)
        if supplier and supplier.must_change_password:
            supplier.must_change_password = False
            supplier.save(update_fields=['must_change_password'])
        return response


@never_cache
@login_required
def dashboard(request):
    # Scope is always derived from the session, never a supplied CNPJ or ID.
    supplier = getattr(request.user, 'supplier', None)
    evaluations = Evaluation.objects.filter(supplier__user=request.user)
    return render(request, 'dashboard.html', {'evaluations': evaluations, 'supplier': supplier})


@never_cache
@user_passes_test(lambda user: user.is_active and user.is_superuser)
def import_csv(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            summary = import_evaluations(form.cleaned_data['file'].read())
        except ValueError as error:
            form.add_error('file', str(error))
        else:
            messages.success(request, f'{summary.evaluations} avaliações importadas; {summary.suppliers_created} fornecedores cadastrados.')
            return redirect('import_csv')
    return render(request, 'form.html', {'form': form, 'title': 'Importar avaliações', 'upload': True})


def mirror_asset(request, filename):
    path = settings.BASE_DIR / 'mirror' / 'assets' / filename
    if Path(filename).name != filename or not path.is_file():
        raise Http404
    types_file = settings.BASE_DIR / 'mirror' / 'asset-types.json'
    types = json.loads(types_file.read_text(encoding='utf-8')) if types_file.exists() else {}
    return FileResponse(path.open('rb'), content_type=types.get(filename))


def public_page(request, page):
    manifest = settings.BASE_DIR / 'mirror' / 'pages.json'
    if not manifest.exists():
        raise Http404
    mapping = json.loads(manifest.read_text(encoding='utf-8'))
    filename = mapping.get('/' + page) or mapping.get('/' + page.rstrip('/') + '/')
    if not filename:
        raise Http404
    response = FileResponse((settings.BASE_DIR / 'mirror' / 'pages' / filename).open('rb'), content_type='text/html; charset=utf-8')
    response['Content-Security-Policy'] = (
        "default-src 'self'; img-src 'self' data:; font-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; form-action 'none'; frame-src 'none'; object-src 'none'; base-uri 'self'"
    )
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response
