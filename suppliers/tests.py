import re
from urllib.parse import urlsplit
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import Client, TestCase, override_settings
from .importer import import_evaluations
from .models import Evaluation, Supplier


class PrivacyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = User.objects.create_user('11222333000181', email='a@example.com', password='Original-pass-932!')
        cls.b = User.objects.create_user('11444777000161', email='b@example.com', password='Original-pass-932!')
        cls.sa = Supplier.objects.create(user=cls.a, name='Fornecedor A', cnpj='11222333000181', email='a@example.com')
        cls.sb = Supplier.objects.create(user=cls.b, name='Fornecedor secreto B', cnpj='11444777000161', email='b@example.com')
        Evaluation.objects.create(supplier=cls.sa, year=2025, score='A')
        Evaluation.objects.create(supplier=cls.sb, year=2024, score='B')

    def test_anonymous_cannot_view_scores(self):
        self.assertEqual(self.client.get('/fornecedores/').status_code, 302)

    def test_supplier_pages_include_full_site_footer(self):
        response = self.client.get('/fornecedores/entrar/')
        self.assertContains(response, 'Mapa do Site')
        self.assertContains(response, 'Destilarias e Processos')
        self.assertContains(response, 'contato@abnequipamentos.com.br')
        self.assertContains(response, 'Visualy Publicidade')
        self.assertContains(response, '--white:#fff')
        self.assertContains(response, '--footer-design:#00032d')
        self.assertContains(response, 'Proibida reprodução ou utilização')

    def test_session_scope_ignores_other_supplier_parameters(self):
        self.client.force_login(self.a)
        response = self.client.get(f'/fornecedores/?cnpj={self.sb.cnpj}&supplier={self.sb.pk}&user={self.b.pk}')
        self.assertContains(response, '<td>A</td>', html=True)
        self.assertNotContains(response, '<td>B</td>', html=True)
        for secret in [self.sb.name, self.sb.cnpj, self.b.username]:
            self.assertNotContains(response, secret)
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertEqual(self.client.get(f'/fornecedores/{self.sb.pk}/').status_code, 404)

    def test_supplier_cannot_import_or_access_admin(self):
        self.client.force_login(self.a)
        self.assertEqual(self.client.get('/fornecedores/importar/').status_code, 302)
        self.assertEqual(self.client.post('/fornecedores/importar/', {'file': SimpleUploadedFile('a.csv', b'cnpj,razaosocial,email,exercicio,nota\n11444777000161,Fornecedor B,b@example.com,2025,99')}).status_code, 302)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(Evaluation.objects.get(supplier=self.sb).score, 'B')

    def test_admin_without_trailing_slash_redirects(self):
        response = self.client.get('/admin')
        self.assertRedirects(response, '/admin/', fetch_redirect_response=False)

    def test_login_and_password_change(self):
        self.a.email = 'novo-contato@example.com'
        self.a.save(update_fields=['email'])
        self.client.post('/fornecedores/entrar/', {'username': '11.222.333/0001-81', 'password': 'Original-pass-932!'})
        self.assertContains(self.client.get('/fornecedores/'), '<td>A</td>', html=True)
        response = self.client.post('/fornecedores/senha/', {'old_password': 'Original-pass-932!', 'new_password1': 'Replacement-pass-943!', 'new_password2': 'Replacement-pass-943!'})
        self.assertEqual(response.status_code, 302)
        self.a.refresh_from_db()
        self.assertTrue(self.a.check_password('Replacement-pass-943!'))
        self.assertFalse(self.a.check_password('Original-pass-932!'))

    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.a)
        self.assertEqual(client.post('/fornecedores/senha/', {}).status_code, 403)

    def test_import_is_atomic(self):
        with self.assertRaises(ValueError):
            import_evaluations(
                b'cnpj,razaosocial,email,exercicio,nota\n'
                b'11222333000181,Fornecedor A,a@example.com,2025,C\n'
                b'99999999999999,Invalido,invalido@example.com,2025,D'
            )
        self.assertEqual(Evaluation.objects.get(supplier=self.sa).score, 'A')

    def test_import_updates_supplier_email_and_accepts_bom_semicolon(self):
        data = ('\ufeffcnpj;razaosocial;email;exercicio;nota\n'
                '11.222.333/0001-81;Fornecedor atualizado;novo@example.com;2025;c').encode('utf-8')
        summary = import_evaluations(data)
        self.assertEqual(summary.evaluations, 1)
        self.assertEqual(Evaluation.objects.get(supplier=self.sa, year=2025).score, 'C')
        self.sa.refresh_from_db()
        self.a.refresh_from_db()
        self.assertEqual(self.sa.name, 'Fornecedor atualizado')
        self.assertEqual(self.sa.email, 'novo@example.com')
        self.assertEqual(self.a.email, 'novo@example.com')

    def test_import_rejects_duplicates_and_oversized_scores(self):
        for rows in [f'11222333000181,Fornecedor A,a@example.com,2025,{"A" * 51}',
                     ('11222333000181,Fornecedor A,a@example.com,2025,A\n'
                      '11222333000181,Fornecedor A,a@example.com,2025,B')]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                import_evaluations(('cnpj,razaosocial,email,exercicio,nota\n' + rows).encode())

    def test_import_accepts_same_supplier_for_different_years(self):
        data = (b'cnpj,razaosocial,email,exercicio,nota\n'
                b'11222333000181,Fornecedor A,a@example.com,2024,B\n'
                b'11222333000181,Fornecedor A,a@example.com,2025,A')
        summary = import_evaluations(data)
        self.assertEqual(summary.evaluations, 2)
        self.assertEqual(Evaluation.objects.get(supplier=self.sa, year=2024).score, 'B')
        self.assertEqual(Evaluation.objects.get(supplier=self.sa, year=2025).score, 'A')

    def test_import_creates_supplier_with_email_and_accepts_division_error_as_null(self):
        summary = import_evaluations(
            b'cnpj,razaosocial,email,exercicio,nota\n'
            b'04252011000110,Novo Fornecedor,novo@example.com,2024,#DIV/0!'
        )
        supplier = Supplier.objects.get(cnpj='04252011000110')
        self.assertEqual(summary.suppliers_created, 1)
        self.assertTrue(supplier.user.check_password('abn@2026'))
        self.assertFalse(supplier.must_change_password)
        self.assertEqual(supplier.email, 'novo@example.com')
        self.assertEqual(supplier.user.email, 'novo@example.com')
        self.assertIsNone(Evaluation.objects.get(supplier=supplier, year=2024).score)

    def test_import_rejects_invalid_cnpj_check_digits(self):
        with self.assertRaisesRegex(ValueError, 'Linha 2: o CNPJ 11222333000182 possui dígitos verificadores inválidos'):
            import_evaluations(
                b'cnpj,razaosocial,email,exercicio,nota\n'
                b'11222333000182,Fornecedor,contato@example.com,2025,10'
            )

    def test_import_reports_the_exact_invalid_field(self):
        header = 'cnpj,razaosocial,email,exercicio,nota\n'
        cases = [
            ((header + ',Fornecedor,contato@example.com,2025,A').encode(), 'o CNPJ está vazio'),
            ((header + '11222333000181,,contato@example.com,2025,A').encode(), 'a razão social está vazia'),
            ((header + '11222333000181,Fornecedor,email-invalido,2025,A').encode(), 'o e-mail'),
            ((header + '11222333000181,Fornecedor,contato@example.com,ano,A').encode(), 'o exercício'),
            ((header + '11222333000181,Fornecedor,contato@example.com,2025').encode(),
             'faltam valores para: nota'),
            ((header + '11222333000181,Fornecedor,contato@example.com,2025,' + 'A' * 51).encode(),
             'a nota excede o limite de 50 caracteres'),
        ]
        for data, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, f'Linha 2: {message}'):
                import_evaluations(data)

    def test_superuser_can_upload(self):
        admin = User.objects.create_superuser('admin', password='Administrator-pass-93!')
        self.client.force_login(admin)
        file = SimpleUploadedFile(
            'scores.csv',
            b'cnpj,razaosocial,email,exercicio,nota\n11222333000181,Fornecedor A,a@example.com,2025,A',
        )
        self.assertEqual(self.client.post('/fornecedores/importar/', {'file': file}).status_code, 302)
        self.assertTrue(Evaluation.objects.filter(supplier=self.sa, year=2025, score='A').exists())

    def test_admin_import_page_and_example_download(self):
        admin = User.objects.create_superuser('admin2', password='Administrator-pass-93!')
        self.client.force_login(admin)
        self.assertEqual(self.client.get('/admin/suppliers/evaluation/importar/').status_code, 200)
        response = self.client.get('/admin/suppliers/evaluation/exemplo.csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(b'cnpj,razaosocial,email,exercicio,nota', response.content)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_admin_reset_creates_test_password_without_forced_change(self):
        admin = User.objects.create_superuser('admin-reset', password='Administrator-pass-93!')
        self.client.force_login(admin)
        url = f'/admin/suppliers/supplier/{self.sa.pk}/resetar-senha/'
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, follow=True)
        reset_message = next(message.message for message in get_messages(response.wsgi_request)
                             if message.message.startswith('Senha temporária:'))
        temporary_password = re.search(r'Senha temporária: (\S+) —', reset_message).group(1)
        self.assertEqual(temporary_password, 'abn@2026')
        self.sa.refresh_from_db()
        self.a.refresh_from_db()
        self.assertFalse(self.sa.must_change_password)
        self.assertTrue(self.a.check_password(temporary_password))
        self.assertEqual(len(mail.outbox), 0)

        self.client.logout()
        response = self.client.post('/fornecedores/entrar/', {
            'username': self.sa.cnpj,
            'password': temporary_password,
        })
        self.assertRedirects(response, '/fornecedores/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/fornecedores/').status_code, 200)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                       PASSWORD_RECOVERY_EMAIL_ENABLED=True)
    def test_password_recovery_uses_cnpj_and_supplier_email_when_enabled(self):
        self.sa.must_change_password = True
        self.sa.save(update_fields=['must_change_password'])
        response = self.client.post('/fornecedores/recuperar-senha/', {'cnpj': self.sa.cnpj})
        self.assertRedirects(response, '/fornecedores/recuperar-senha/enviado/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/fornecedores/recuperar-senha/', mail.outbox[0].body)
        reset_url = re.search(r'https?://\S+', mail.outbox[0].body).group(0)
        response = self.client.get(urlsplit(reset_url).path)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(response.url, {
            'new_password1': 'Recovered-pass-951!',
            'new_password2': 'Recovered-pass-951!',
        })
        self.assertRedirects(response, '/fornecedores/recuperar-senha/concluido/')
        self.sa.refresh_from_db()
        self.a.refresh_from_db()
        self.assertFalse(self.sa.must_change_password)
        self.assertTrue(self.a.check_password('Recovered-pass-951!'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                       PASSWORD_RECOVERY_EMAIL_ENABLED=False)
    def test_password_recovery_sends_no_email_during_testing(self):
        response = self.client.post('/fornecedores/recuperar-senha/', {'cnpj': self.sa.cnpj})
        self.assertRedirects(response, '/fornecedores/recuperar-senha/enviado/')
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.get('/fornecedores/recuperar-senha/enviado/')
        self.assertContains(response, 'nenhum e-mail será enviado durante esta fase de testes')

    def test_supplier_email_is_synchronized_to_login_user(self):
        self.sa.email = 'financeiro@example.com'
        self.sa.save(update_fields=['email'])
        self.a.refresh_from_db()
        self.assertEqual(self.a.email, 'financeiro@example.com')
