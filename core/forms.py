# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Holding, ProcessoHolding, Documento
from decimal import Decimal
from django.utils import timezone

class CustomSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'cliente'
        if commit:
            user.save()
        return user

class SimulationForm(forms.Form):
    number_of_properties = forms.IntegerField(
        label="Quantos imóveis você possui?", min_value=0, required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao'})
    )
    total_property_value = forms.DecimalField(
        label="Qual o valor total dos imóveis? (R$)", max_digits=15, decimal_places=2, min_value=Decimal('0.01'), required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': '0.00'})
    )
    has_companies = forms.ChoiceField(
        label="Você possui empresas?", choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True, initial='no'
    )
    number_of_companies = forms.IntegerField(
        label="Quantas empresas você possui?", min_value=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao'})
    )
    company_tax_regime = forms.ChoiceField(
        label="Qual o regime tributário da(s) empresa(s)?",
        choices=[('', '---------'), ('simples', 'Simples Nacional'), ('presumido', 'Lucro Presumido'), ('real', 'Lucro Real')],
        widget=forms.RadioSelect, required=False
    )
    monthly_profit = forms.DecimalField(
        label="Qual o lucro mensal médio distribuído? (R$)", max_digits=15, decimal_places=2, min_value=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': '0.00'})
    )
    receives_rent = forms.ChoiceField(
        label="Você recebe aluguéis de imóveis?", choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True, initial='no'
    )
    monthly_rent = forms.DecimalField(
        label="Qual o valor mensal total dos aluguéis? (R$)", max_digits=15, decimal_places=2, min_value=Decimal('0.01'), required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': '0.00'})
    )
    number_of_heirs = forms.IntegerField(
        label="Quantos herdeiros você tem (filhos, cônjuge, etc.)?", min_value=0, required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao'})
    )
    avoid_conflicts = forms.ChoiceField(
        label="Você gostaria de evitar conflitos familiares e deixar tudo organizado?",
        choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True, initial='no'
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

        if number_of_properties is not None and number_of_properties > 0:
            if not total_property_value or total_property_value <= 0:
                self.add_error('total_property_value', "Com imóveis, o valor total deve ser informado e maior que zero.")
        else:
            cleaned_data['total_property_value'] = Decimal('0')


        if has_companies == 'yes':
            if number_of_companies is None or number_of_companies <= 0:
                self.add_error('number_of_companies', "Se possui empresas, informe a quantidade.")
            if not company_tax_regime:
                self.add_error('company_tax_regime', "Se possui empresas, informe o regime tributário.")
            if monthly_profit is None:
                self.add_error('monthly_profit', "Se possui empresas, informe o lucro mensal (pode ser 0).")
            elif monthly_profit < 0:
                self.add_error('monthly_profit', "O lucro mensal não pode ser negativo.")
        else:
            cleaned_data['number_of_companies'] = 0
            cleaned_data['company_tax_regime'] = ''
            cleaned_data['monthly_profit'] = Decimal('0')

        if receives_rent == 'yes':
            if not monthly_rent or monthly_rent <= 0:
                self.add_error('monthly_rent', "Se recebe aluguéis, o valor mensal deve ser informado e maior que zero.")
        else:
            cleaned_data['monthly_rent'] = Decimal('0')
            
        return cleaned_data


class HoldingCreationUserForm(forms.ModelForm):
    nome_holding = forms.CharField(
        label="Nome que você gostaria para sua Holding",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Holding Familiar Silva'})
    )

    class Meta:
        model = Holding
        fields = ['nome_holding']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['nome_holding'].widget.attrs.update({'class': 'form-control-custom'})
        if user and user.is_authenticated and not self.initial.get('nome_holding'):
            default_name = f"Holding de {user.first_name}" if user.first_name else "Minha Holding Patrimonial"
            self.initial['nome_holding'] = default_name
            self.fields['nome_holding'].widget.attrs['placeholder'] = default_name


class ConsultantCreationForm(forms.ModelForm):
    email = forms.EmailField(
        label="E-mail do Consultor", required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'exemplo@dominio.com', 'class': 'form-control'})
    )
    first_name = forms.CharField(label="Nome", max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class': 'form-control'}), help_text="Crie uma senha forte para o consultor.")
    confirm_password = forms.CharField(label="Confirmar Senha", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este endereço de e-mail já está em uso.")
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise ValidationError("As senhas não coincidem.")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.user_type = 'consultor'
        user.is_staff = False 
        user.is_active = True
        if commit:
            user.save()
        return user

# ### FORMULÁRIO ATUALIZADO ###
class AssignConsultantAndHoldingDetailsForm(forms.ModelForm):
    nome_holding = forms.CharField(label="Nome da Holding", max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label="Descrição da Holding", widget=forms.Textarea(attrs={'rows':3, 'class': 'form-control'}), required=False)
    
    consultores = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(user_type='consultor', is_active=True).order_by('first_name', 'last_name'),
        required=False,
        label="Consultores Responsáveis",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input-group'}), # Mais amigável para M2M
        help_text="Selecione um ou mais consultores. Desmarque todos para remover."
    )

    class Meta:
        model = Holding
        fields = ['nome_holding', 'description', 'consultores']
# ### FIM DO FORMULÁRIO ATUALIZADO ###

class ProcessStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = ProcessoHolding
        fields = ['status_atual', 'observacoes']
        widgets = {
            'status_atual': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'status_atual': 'Novo Status do Processo:',
            'observacoes': 'Adicionar Observações (visível para equipe interna):'
        }

class HoldingOfficializeForm(forms.ModelForm):
    data_oficializacao = forms.DateField(
        label="Data de Oficialização Legal",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        initial=timezone.now().date
    )
    class Meta:
        model = Holding
        fields = ['data_oficializacao']

    def clean_data_oficializacao(self):
        data = self.cleaned_data.get('data_oficializacao')
        if data and data > timezone.now().date():
            raise ValidationError("A data de oficialização não pode ser no futuro.")
        return data

class AddClientToHoldingForm(forms.Form):
    email = forms.EmailField(
        label="E-mail do Cliente a Adicionar",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'cliente@exemplo.com'}),
        help_text="O cliente já deve possuir uma conta na plataforma e ser do tipo 'cliente'."
    )

    def clean_email(self):
        email_str = self.cleaned_data.get('email')
        if not email_str:
            raise ValidationError("E-mail é obrigatório.") 
        
        email_cleaned = email_str.lower()
        try:
            user = User.objects.get(email=email_cleaned, user_type='cliente')
            if not user.is_active:
                raise ValidationError("A conta deste cliente não está ativa.")
        except User.DoesNotExist:
            raise ValidationError("Nenhum cliente ativo encontrado com este e-mail na plataforma.")
        return user
    
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nome_documento_logico', 'arquivo', 'categoria', 'descricao_adicional']
        widgets = {
            'nome_documento_logico': forms.TextInput(attrs={'class': 'form-control-custom', 'placeholder': 'Ex: Contrato Social da Holding X'}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control-custom'}),
            'categoria': forms.Select(attrs={'class': 'form-control-custom'}),
            'descricao_adicional': forms.Textarea(attrs={'class': 'form-control-custom', 'rows': 3, 'placeholder': 'Opcional: Descreva brevemente o documento ou a versão.'}),
        }
        labels = {
            'nome_documento_logico': 'Nome/Tipo do Documento',
            'arquivo': 'Selecione o Arquivo',
            'categoria': 'Categoria do Documento',
            'descricao_adicional': 'Descrição/Observações da Versão (Opcional)',
        }
        help_texts = {
            'nome_documento_logico': 'Use um nome claro que identifique o documento. Todas as versões deste documento serão agrupadas sob este nome.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['arquivo'].widget.attrs.update({'lang': 'pt-br'})


class ManagementDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nome_documento_logico', 'arquivo', 'categoria', 'descricao_adicional']
        widgets = {
            'nome_documento_logico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Contrato Social da Holding X'}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'descricao_adicional': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opcional: Descreva brevemente o documento ou a versão.'}),
        }
        labels = {
            'nome_documento_logico': 'Nome/Tipo do Documento',
            'arquivo': 'Selecione o Arquivo',
            'categoria': 'Categoria do Documento',
            'descricao_adicional': 'Descrição/Observações da Versão (Opcional)',
        }
        help_texts = {
            'nome_documento_logico': 'Use um nome claro que identifique o documento. Todas as versões deste documento serão agrupadas sob este nome.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['arquivo'].widget.attrs.update({'lang': 'pt-br'})