from django.contrib import admin
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from .forms import UploadForm
from .importer import import_evaluations
from .models import Evaluation, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'email', 'access_status')
    search_fields = ('name', 'cnpj', 'email', 'user__username')
    fields = ('name', 'cnpj', 'email', 'user', 'must_change_password')

    def get_urls(self):
        return [
            path('<int:supplier_id>/resetar-senha/', self.admin_site.admin_view(self.reset_password_view),
                 name='suppliers_supplier_reset_password'),
        ] + super().get_urls()

    @admin.display(description='Acesso')
    def access_status(self, supplier):
        url = reverse('admin:suppliers_supplier_reset_password', args=[supplier.pk])
        label = 'Resetar senha' if supplier.user.has_usable_password() else 'Criar senha temporária'
        return format_html('<a href="{}">{}</a>', url, label)

    def reset_password_view(self, request, supplier_id):
        supplier = self.get_object(request, supplier_id)
        if supplier is None or not self.has_change_permission(request, supplier):
            raise PermissionDenied
        if request.method == 'POST':
            temporary_password = 'abn@2026'
            supplier.user.set_password(temporary_password)
            supplier.user.save(update_fields=['password'])
            supplier.must_change_password = False
            supplier.save(update_fields=['must_change_password'])
            email_sent = False
            if settings.PASSWORD_RECOVERY_EMAIL_ENABLED and supplier.email:
                email_sent = bool(send_mail(
                    'Senha temporária — Área do fornecedor ABN',
                    f'Olá, {supplier.name}.\n\nSua senha de acesso é: {temporary_password}\n'
                    'Acesse a Área do fornecedor usando seu CNPJ.\n',
                    None,
                    [supplier.email],
                    fail_silently=True,
                ))
            delivery = 'O e-mail foi enviado.' if email_sent else 'O e-mail não foi enviado; informe a senha ao fornecedor.'
            self.message_user(
                request,
                f'Senha temporária: {temporary_password} — {delivery} Ela será exibida somente nesta mensagem.',
                messages.WARNING,
            )
            return redirect('admin:suppliers_supplier_changelist')
        context = {
            **self.admin_site.each_context(request),
            'title': 'Gerar senha temporária',
            'supplier': supplier,
            'opts': self.model._meta,
        }
        return render(request, 'admin/suppliers/supplier/reset_password.html', context)


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'year', 'score')
    list_filter = ('year',)
    change_list_template = 'admin/suppliers/evaluation/change_list.html'

    def get_urls(self):
        return [
            path('importar/', self.admin_site.admin_view(self.import_view), name='suppliers_evaluation_import'),
            path('exemplo.csv', self.admin_site.admin_view(self.example_csv), name='suppliers_evaluation_example'),
        ] + super().get_urls()

    def import_view(self, request):
        form = UploadForm(request.POST or None, request.FILES or None)
        if request.method == 'POST' and form.is_valid():
            try:
                summary = import_evaluations(form.cleaned_data['file'].read())
            except ValueError as error:
                form.add_error('file', str(error))
            else:
                self.message_user(
                    request,
                    f'{summary.evaluations} avaliações importadas; '
                    f'{summary.suppliers_created} fornecedores cadastrados.',
                    messages.SUCCESS,
                )
                return redirect('admin:suppliers_evaluation_changelist')
        context = {
            **self.admin_site.each_context(request),
            'title': 'Importar fornecedores e avaliações',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/suppliers/evaluation/import.html', context)

    def example_csv(self, request):
        content = '\ufeffcnpj,razaosocial,nota\r\n11222333000181,Fornecedor Exemplo,A\r\n'
        response = HttpResponse(content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="exemplo-avaliacoes.csv"'
        return response


admin.site.site_header = 'ABN · Administração de fornecedores'
