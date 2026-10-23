from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from suppliers.models import Supplier


class Command(BaseCommand):
    help = 'Cadastra fornecedor com CNPJ e senha inicial padrão.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--cnpj', required=True)
        parser.add_argument('--name', required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        cnpj = ''.join(character for character in options['cnpj'] if character.isdigit())
        if len(cnpj) != 14:
            raise CommandError('O CNPJ deve conter 14 dígitos.')
        user = User(username=cnpj, email=email)
        try:
            user.full_clean(exclude=['password'])
            user.set_password('abn@2026')
            user.save()
            supplier = Supplier(user=user, name=options['name'], cnpj=cnpj, email=email,
                                must_change_password=False)
            supplier.full_clean()
            supplier.save()
        except (ValidationError, IntegrityError) as error:
            raise CommandError(str(error))
        self.stdout.write(self.style.SUCCESS('Fornecedor cadastrado.'))
