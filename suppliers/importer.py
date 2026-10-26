import csv
import io
import re
from dataclasses import dataclass
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from .models import Evaluation, Supplier, validate_cnpj


@dataclass(frozen=True)
class ImportSummary:
    evaluations: int
    suppliers_created: int


def parse_score(value):
    normalized = value.strip().upper()
    if not normalized or 'DIV/0' in normalized:
        return None
    if len(normalized) > 50:
        raise ValueError('a nota excede o limite de 50 caracteres.')
    return normalized


def parse_email(value):
    email = value.strip().lower()
    if not email:
        raise ValueError('o e-mail está vazio.')
    try:
        validate_email(email)
    except ValidationError:
        raise ValueError(f'o e-mail "{value.strip()}" é inválido.')
    return email


def parse_year(value):
    raw = value.strip()
    if not raw:
        raise ValueError('o exercício está vazio.')
    if len(raw) != 4 or not raw.isdigit():
        raise ValueError(f'o exercício "{raw}" deve ser um ano com quatro dígitos.')
    year = int(raw)
    if year < 1900 or year > 9999:
        raise ValueError('o exercício deve estar entre 1900 e 9999.')
    return year


def parse_cnpj(value):
    raw = value.strip()
    if not raw:
        raise ValueError('o CNPJ está vazio.')
    if re.search(r'[^0-9./\-\s]', raw):
        raise ValueError(f'o CNPJ "{raw}" contém caracteres inválidos.')
    cnpj = re.sub(r'[./\-\s]', '', raw)
    if len(cnpj) != 14:
        raise ValueError(f'o CNPJ deve ter 14 dígitos; foram encontrados {len(cnpj)}.')
    try:
        validate_cnpj(cnpj)
    except ValidationError:
        raise ValueError(f'o CNPJ {raw} possui dígitos verificadores inválidos.')
    return cnpj


@transaction.atomic
def import_evaluations(data):
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('Use CSV com codificação UTF-8.')
    reader = csv.DictReader(io.StringIO(text), delimiter=';' if ';' in text.split('\n')[0] else ',')
    if reader.fieldnames:
        reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]
    expected_fields = ['cnpj', 'razaosocial', 'email', 'exercicio', 'nota']
    if reader.fieldnames != expected_fields:
        raise ValueError('O cabeçalho deve ser cnpj,razaosocial,email,exercicio,nota (nesta ordem).')
    seen = set()
    count = 0
    suppliers_created = 0
    User = get_user_model()
    for line, row in enumerate(reader, start=2):
        if line > 10001:
            raise ValueError('Limite de 10.000 linhas excedido.')
        try:
            if None in row:
                raise ValueError('há colunas adicionais. Se um valor contém vírgula, coloque-o entre aspas.')
            missing = [field for field, value in row.items() if value is None]
            if missing:
                raise ValueError(f'faltam valores para: {", ".join(missing)}.')
            cnpj = parse_cnpj(row['cnpj'])
            name = row['razaosocial'].strip()
            if not name:
                raise ValueError('a razão social está vazia.')
            if len(name) > 200:
                raise ValueError('a razão social excede o limite de 200 caracteres.')
            email = parse_email(row['email'])
            year = parse_year(row['exercicio'])
            score = parse_score(row['nota'])
        except ValueError as error:
            raise ValueError(f'Linha {line}: {error}')
        evaluation_key = (cnpj, year)
        if evaluation_key in seen:
            raise ValueError(f'Linha {line}: CNPJ e exercício duplicados no arquivo.')
        seen.add(evaluation_key)
        if Supplier.objects.exclude(cnpj=cnpj).filter(email__iexact=email).exists():
            raise ValueError(f'Linha {line}: o e-mail {email} já pertence a outro fornecedor.')
        supplier = Supplier.objects.filter(cnpj=cnpj).first()
        if supplier is None:
            user, _ = User.objects.get_or_create(username=cnpj)
            user.email = email
            user.set_password('abn@2026')
            user.save(update_fields=['email', 'password'])
            supplier = Supplier(user=user, name=name, cnpj=cnpj, email=email)
            supplier.full_clean()
            supplier.must_change_password = False
            supplier.save()
            suppliers_created += 1
        else:
            changed_fields = []
            if supplier.name != name:
                supplier.name = name
                changed_fields.append('name')
            if supplier.email != email:
                supplier.email = email
                changed_fields.append('email')
            if changed_fields:
                supplier.save(update_fields=changed_fields)
        Evaluation.objects.update_or_create(supplier=supplier, year=year, defaults={'score': score})
        count += 1
    if not count:
        raise ValueError('O arquivo não contém avaliações.')
    return ImportSummary(evaluations=count, suppliers_created=suppliers_created)
