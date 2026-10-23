from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


def validate_cnpj(value):
    digits = ''.join(character for character in value if character.isdigit())
    if len(digits) != 14 or digits == digits[0] * 14:
        raise ValidationError('CNPJ inválido.')
    numbers = [int(character) for character in digits]
    for length, weights in ((12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]),
                            (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])):
        remainder = sum(number * weight for number, weight in zip(numbers[:length], weights)) % 11
        digit = 0 if remainder < 2 else 11 - remainder
        if numbers[length] != digit:
            raise ValidationError('CNPJ inválido.')


class Supplier(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='supplier')
    name = models.CharField('Razão social', max_length=200)
    cnpj = models.CharField('CNPJ (14 dígitos, sem pontuação)', max_length=14, unique=True,
                            validators=[RegexValidator(r'^\d{14}$', 'Informe 14 dígitos.'), validate_cnpj])
    email = models.EmailField('E-mail para recuperação de senha', unique=True, null=True, blank=True)
    must_change_password = models.BooleanField('Exigir nova senha no próximo acesso', default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        email = self.email or ''
        if self.user.email != email:
            type(self.user).objects.filter(pk=self.user_id).update(email=email)
            self.user.email = email

    def __str__(self):
        return self.name


class Evaluation(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='evaluations')
    year = models.PositiveSmallIntegerField('Exercício')
    score = models.CharField('Nota', max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-year']
        constraints = [models.UniqueConstraint(fields=['supplier', 'year'], name='unique_supplier_year'),
                       models.CheckConstraint(condition=models.Q(year__gte=1900, year__lte=9999), name='valid_year')]
