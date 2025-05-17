from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email

class HoldingForm(forms.Form):
    company_name = forms.CharField(max_length=100, required=True)
    owner_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    number_of_properties = forms.IntegerField(min_value=0, required=True)
    number_of_companies = forms.IntegerField(min_value=0, required=True)
    message = forms.CharField(widget=forms.Textarea, required=False)

class SimulationForm(forms.Form):
    number_of_properties = forms.IntegerField(
        label="Quantos imóveis você possui?",
        min_value=0,
        required=True
    )
    total_property_value = forms.DecimalField(
        label="Qual o valor total dos imóveis? (R$)",
        max_digits=15,
        decimal_places=2,
        min_value=0,
        required=False
    )
    has_companies = forms.ChoiceField(
        label="Você possui empresas?",
        choices=[('yes', 'Sim'), ('no', 'Não')],
        widget=forms.RadioSelect,
        required=True
    )
    number_of_companies = forms.IntegerField(
        label="Quantas empresas você possui?",
        min_value=0,
        required=False
    )
    company_tax_regime = forms.ChoiceField(
        label="Qual o regime tributário da(s) empresa(s)?",
        choices=[
            ('simples', 'Simples Nacional'),
            ('presumido', 'Lucro Presumido'),
            ('real', 'Lucro Real')
        ],
        widget=forms.RadioSelect,
        required=False
    )
    monthly_profit = forms.DecimalField(
        label="Qual o lucro mensal médio distribuído? (R$)",
        max_digits=15,
        decimal_places=2,
        min_value=0,
        required=False
    )
    receives_rent = forms.ChoiceField(
        label="Você recebe aluguéis de imóveis?",
        choices=[('yes', 'Sim'), ('no', 'Não')],
        widget=forms.RadioSelect,
        required=True
    )
    monthly_rent = forms.DecimalField(
        label="Qual o valor mensal total dos aluguéis? (R$)",
        max_digits=15,
        decimal_places=2,
        min_value=0,
        required=False
    )
    number_of_heirs = forms.IntegerField(
        label="Quantos herdeiros você tem (filhos, cônjuge, etc.)?",
        min_value=0,
        required=True
    )
    avoid_conflicts = forms.ChoiceField(
        label="Você gostaria de evitar conflitos familiares e deixar tudo organizado?",
        choices=[('yes', 'Sim'), ('no', 'Não')],
        widget=forms.RadioSelect,
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        number_of_properties = cleaned_data.get('number_of_properties')
        total_property_value = cleaned_data.get('total_property_value')
        has_companies = cleaned_data.get('has_companies')
        number_of_companies = cleaned_data.get('number_of_companies')
        company_tax_regime = cleaned_data.get('company_tax_regime')
        monthly_profit = cleaned_data.get('monthly_profit')
        receives_rent = cleaned_data.get('receives_rent')
        monthly_rent = cleaned_data.get('monthly_rent')

        if number_of_properties and number_of_properties > 0:
            if not total_property_value:
                self.add_error('total_property_value', "Este campo é obrigatório quando você possui imóveis.")
            elif total_property_value <= 0:
                self.add_error('total_property_value', "O valor total dos imóveis deve ser maior que zero.")

        if has_companies == 'yes':
            if number_of_companies is None or number_of_companies <= 0:
                self.add_error('number_of_companies', "Este campo é obrigatório quando você possui empresas.")
            if not company_tax_regime:
                self.add_error('company_tax_regime', "Este campo é obrigatório quando você possui empresas.")
            if monthly_profit is None:
                self.add_error('monthly_profit', "Este campo é obrigatório quando você possui empresas.")
            elif monthly_profit < 0:
                self.add_error('monthly_profit', "O lucro mensal não pode ser negativo.")

        if receives_rent == 'yes':
            if monthly_rent is None:
                self.add_error('monthly_rent', "Este campo é obrigatório quando você recebe aluguéis.")
            elif monthly_rent <= 0:
                self.add_error('monthly_rent', "O valor dos aluguéis deve ser maior que zero.")

        return cleaned_data