from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from .models import Supplier, validate_cnpj


class CNPJLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='CNPJ',
        max_length=18,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocomplete': 'username',
            'inputmode': 'numeric',
            'placeholder': '00.000.000/0000-00',
            'maxlength': '18',
            'data-cnpj-mask': 'true',
        }),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].widget.attrs['maxlength'] = '18'

    def clean_username(self):
        cnpj = ''.join(character for character in self.cleaned_data['username'] if character.isdigit())
        if len(cnpj) != 14:
            raise forms.ValidationError('Informe um CNPJ com 14 dígitos.')
        return cnpj


class CNPJPasswordResetForm(forms.Form):
    cnpj = forms.CharField(
        label='CNPJ',
        max_length=18,
        widget=forms.TextInput(attrs={'autofocus': True, 'inputmode': 'numeric',
                                      'placeholder': '00.000.000/0000-00', 'maxlength': '18',
                                      'data-cnpj-mask': 'true'}),
    )

    def clean_cnpj(self):
        cnpj = ''.join(character for character in self.cleaned_data['cnpj'] if character.isdigit())
        try:
            validate_cnpj(cnpj)
        except ValidationError:
            raise forms.ValidationError('Informe um CNPJ válido.')
        return cnpj

    def save(self, **kwargs):
        if not settings.PASSWORD_RECOVERY_EMAIL_ENABLED:
            return
        supplier = Supplier.objects.select_related('user').filter(cnpj=self.cleaned_data['cnpj']).first()
        if not supplier or not supplier.email:
            return
        reset_form = PasswordResetForm({'email': supplier.email})
        if reset_form.is_valid():
            reset_form.save(**kwargs)


class UploadForm(forms.Form):
    file = forms.FileField(label='CSV de avaliações')

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 2 * 1024 * 1024:
            raise forms.ValidationError('O limite é 2 MB.')
        return file
