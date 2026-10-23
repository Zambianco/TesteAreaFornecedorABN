import csv
import io
import re
from dataclasses import dataclass
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
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
def import_evaluations(data, year=None):
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('Use CSV com codificação UTF-8.')
    reader = csv.DictReader(io.StringIO(text), delimiter=';' if ';' in text.split('\n')[0] else ',')
    if reader.fieldnames:
        reader.fieldnames = [field.strip().lower() for field in reader.fieldnames]
    if reader.fieldnames != ['cnpj', 'razaosocial', 'nota']:
        raise ValueError('O cabeçalho deve ser cnpj,razaosocial,nota (nesta ordem).')
    year = year or timezone.localdate().year
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
            score = parse_score(row['nota'])
        except ValueError as error:
            raise ValueError(f'Linha {line}: {error}')
        if cnpj in seen:
            raise ValueError(f'Linha {line}: CNPJ duplicado no arquivo.')
        seen.add(cnpj)
        supplier = Supplier.objects.filter(cnpj=cnpj).first()
        if supplier is None:
            user, _ = User.objects.get_or_create(username=cnpj)
            user.set_password('abn@2026')
            user.save(update_fields=['password'])
            supplier = Supplier(user=user, name=name, cnpj=cnpj, email=user.email or None)
            supplier.full_clean()
            supplier.must_change_password = False
            supplier.save()
            suppliers_created += 1
        elif supplier.name != name:
            supplier.name = name
            supplier.save(update_fields=['name'])
        Evaluation.objects.update_or_create(supplier=supplier, year=year, defaults={'score': score})
        count += 1
    if not count:
        raise ValueError('O arquivo não contém avaliações.')
    return ImportSummary(evaluations=count, suppliers_created=suppliers_created)
