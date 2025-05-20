# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm # Para CustomSignupForm
from django.core.exceptions import ValidationError
from .models import User, Holding # Seu User customizado e Holding
from decimal import Decimal
from .models import User, Holding, ProcessoHolding, Documento
from django.utils import timezone
# Seu formulário de cadastro customizado.
# Lembre-se: se for usar este, defina ACCOUNT_SIGNUP_FORM_CLASS em settings.py.
# Caso contrário, o allauth.account.forms.SignupForm será usado pela view signup.
class CustomSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    # A senha e confirmação de senha são herdadas do UserCreationForm

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name") # email é o USERNAME_FIELD

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'cliente' # Define o tipo de usuário padrão
        # A senha já é hasheada e tratada pelo UserCreationForm.save()
        if commit:
            user.save()
        return user

# Formulário para a página de simulação do cliente
class SimulationForm(forms.Form):
    number_of_properties = forms.IntegerField(
        label="Quantos imóveis você possui?", min_value=0, required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao'})
    )
    total_property_value = forms.DecimalField(
        label="Qual o valor total dos imóveis? (R$)", max_digits=15, decimal_places=2, min_value=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': '0.00'})
    )
    has_companies = forms.ChoiceField(
        label="Você possui empresas?", choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True
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
        widget=forms.RadioSelect, required=True
    )
    monthly_rent = forms.DecimalField(
        label="Qual o valor mensal total dos aluguéis? (R$)", max_digits=15, decimal_places=2, min_value=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': '0.00'})
    )
    number_of_heirs = forms.IntegerField(
        label="Quantos herdeiros você tem (filhos, cônjuge, etc.)?", min_value=0, required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao'})
    )
    avoid_conflicts = forms.ChoiceField(
        label="Você gostaria de evitar conflitos familiares e deixar tudo organizado?",
        choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True
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
            if not total_property_value or total_property_value <= 0:
                self.add_error('total_property_value', "Com imóveis, o valor total deve ser informado e maior que zero.")
        
        if has_companies == 'yes':
            if not number_of_companies or number_of_companies <= 0:
                self.add_error('number_of_companies', "Se possui empresas, informe a quantidade.")
            if not company_tax_regime:
                self.add_error('company_tax_regime', "Se possui empresas, informe o regime tributário.")
            if monthly_profit is None: # Lucro pode ser 0, mas o campo deve ser enviado
                 self.add_error('monthly_profit', "Se possui empresas, informe o lucro mensal (pode ser 0).")
            elif monthly_profit < 0: # Não pode ser negativo
                self.add_error('monthly_profit', "O lucro mensal não pode ser negativo.")
        else: # Se não tem empresas, define valores padrão para os campos dependentes
            cleaned_data['number_of_companies'] = 0
            cleaned_data['company_tax_regime'] = None # ou '' se preferir
            cleaned_data['monthly_profit'] = Decimal('0')

        if receives_rent == 'yes':
            if not monthly_rent or monthly_rent <= 0:
                self.add_error('monthly_rent', "Se recebe aluguéis, o valor mensal deve ser informado e maior que zero.")
        else: # Se não recebe aluguel, define valor padrão
            cleaned_data['monthly_rent'] = Decimal('0')
            
        return cleaned_data

# Formulário simplificado para o cliente iniciar a criação de uma Holding
class HoldingCreationUserForm(forms.ModelForm):
    nome_holding = forms.CharField(
        label="Nome que você gostaria para sua Holding",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Holding Familiar Silva'})
    )

    class Meta:
        model = Holding
        fields = ['nome_holding'] # Apenas o nome da holding

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Aplica a classe CSS customizada ao campo nome_holding
        self.fields['nome_holding'].widget.attrs.update(
            {'class': 'form-control-custom'}
        )

        # Preenche o nome da holding com uma sugestão se o usuário estiver logado e o campo não tiver valor inicial
        if user and user.is_authenticated and not self.initial.get('nome_holding'):
            default_name = f"Holding de {user.first_name}" if user.first_name else "Minha Holding Patrimonial"
            self.initial['nome_holding'] = default_name
            self.fields['nome_holding'].widget.attrs['placeholder'] = default_name


# Formulário para o superusuário criar Consultores
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

# Formulário para atribuir consultor a uma Holding e editar detalhes básicos da Holding
class AssignConsultantToHoldingForm(forms.ModelForm):
    nome_holding = forms.CharField(label="Nome da Holding", max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label="Descrição da Holding", widget=forms.Textarea(attrs={'rows':3, 'class': 'form-control'}), required=False)
    consultor_responsavel = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='consultor', is_active=True),
        required=False,
        label="Consultor Responsável",
        empty_label="---- Nenhum (Remover Consultor) ----",
        widget=forms.Select(attrs={'class': 'form-control'}) # ou form-select se usar Bootstrap/Tailwind
    )

    class Meta:
        model = Holding
        fields = ['nome_holding', 'description', 'consultor_responsavel']

class ProcessStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = ProcessoHolding
        fields = ['status_atual', 'observacoes'] # Incluindo observações
        widgets = {
            'status_atual': forms.Select(attrs={'class': 'form-control'}), # Use sua classe de estilo de management
            'observacoes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'status_atual': 'Novo Status do Processo:',
            'observacoes': 'Adicionar Observações (visível para equipe interna):'
        }

class HoldingOfficializeForm(forms.ModelForm):
    data_oficializacao = forms.DateField(
        label="Data de Oficialização Legal",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), # Classe de estilo management
        required=True,
        initial=timezone.now().date # Sugere a data atual
    )
    class Meta:
        model = Holding
        fields = ['data_oficializacao'] # 'is_legally_official' será definido na view

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
            # Isso não deveria acontecer se o campo for required=True (padrão), mas por segurança.
            raise ValidationError("E-mail é obrigatório.") 
        
        email_cleaned = email_str.lower()
        try:
            # Busca por um usuário que seja do tipo cliente e esteja ativo
            user = User.objects.get(email=email_cleaned, user_type='cliente')
            if not user.is_active:
                raise ValidationError("A conta deste cliente não está ativa.")
        except User.DoesNotExist:
            raise ValidationError("Nenhum cliente ativo encontrado com este e-mail na plataforma.")
        return user # Retorna o objeto User do cliente completo
    
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nome_documento_logico', 'arquivo', 'categoria', 'descricao_adicional']
        widgets = {
            'nome_documento_logico': forms.TextInput(attrs={'class': 'form-control-custom', 'placeholder': 'Ex: Contrato Social da Holding X'}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control-custom'}), # Permite limpar o arquivo
            'categoria': forms.Select(attrs={'class': 'form-control-custom'}),
            'descricao_adicional': forms.Textarea(attrs={'class': 'form-control-custom', 'rows': 3, 'placeholder': 'Opcional: Descreva brevemente o documento ou a versão.'}),
        }
        labels = {
            'nome_documento_logico': 'Nome/Tipo do Documento', # Rótulo ajustado
            'arquivo': 'Selecione o Arquivo',
            'categoria': 'Categoria do Documento',
            'descricao_adicional': 'Descrição/Observações da Versão (Opcional)',
        }
        help_texts = {
            'nome_documento_logico': 'Use um nome claro que identifique o documento, como "Contrato Social Holding XPTO" ou "RG Sócio João". Todas as versões deste documento serão agrupadas sob este nome.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['arquivo'].widget.attrs.update({'lang': 'pt-br'}) # Para tradução do botão "Escolher arquivo"


# Formulário para Admin/Consultor, pode usar classes CSS diferentes se necessário
class ManagementDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nome_documento_logico', 'arquivo', 'categoria', 'descricao_adicional']
        widgets = { # Use as classes CSS do painel de gestão
            'nome_documento_logico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Contrato Social da Holding X'}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'descricao_adicional': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opcional: Descreva brevemente o documento ou a versão.'}),
        }
        labels = { # Rótulos podem ser os mesmos
            'nome_documento_logico': 'Nome/Tipo do Documento',
            'arquivo': 'Selecione o Arquivo',
            'categoria': 'Categoria do Documento',
            'descricao_adicional': 'Descrição/Observações da Versão (Opcional)',
        }
        help_texts = {
            'nome_documento_logico': 'Use um nome claro que identifique o documento, como "Contrato Social Holding XPTO" ou "RG Sócio João". Todas as versões deste documento serão agrupadas sob este nome.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['arquivo'].widget.attrs.update({'lang': 'pt-br'})