# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Holding, ProcessoHolding, Documento,ChatMessage,PastaDocumento
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
    BRAZIL_STATES = [
        ('', 'Selecione um estado'),
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ]

    number_of_properties = forms.IntegerField(
        label="Quantos imóveis você possui?", min_value=0, required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': 'Ex.: 2'})
    )
    total_property_value = forms.DecimalField(
        label="Qual o valor estimado total dos seus imóveis? (R$)", max_digits=15, decimal_places=2, min_value=Decimal('0.01'), required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': 'Ex.: 1.500.000,00'}),
        help_text="Inclua o valor de mercado aproximado de todos os imóveis."
    )
    property_state = forms.ChoiceField(
        label="Em qual estado estão localizados a maioria dos seus imóveis?",
        choices=BRAZIL_STATES, required=False,
        widget=forms.Select(attrs={'class': 'form-control-simulacao'})
    )
    has_companies = forms.ChoiceField(
        label="Você possui empresas?", choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True, initial='no'
    )
    number_of_companies = forms.IntegerField(
        label="Quantas empresas você possui?", min_value=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': 'Ex.: 1'})
    )
    company_tax_regime = forms.ChoiceField(
        label="Qual o tipo de tributação da(s) sua(s) empresa(s)?",
        choices=[('unknown', 'Não sei informar'), ('simples', 'Simples Nacional'), ('presumido', 'Lucro Presumido'), ('real', 'Lucro Real')],
        widget=forms.RadioSelect, required=False,
        help_text="Se não souber, selecione 'Não sei informar'. Consulte seu contador."
    )
    monthly_profit = forms.DecimalField(
        label="Qual o lucro mensal médio que você retira da(s) empresa(s)? (R$)", max_digits=15, decimal_places=2, min_value=0, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': 'Ex.: 10.000,00'})
    )
    has_investments = forms.ChoiceField(
        label="Você possui outros investimentos financeiros relevantes (ex.: ações, fundos, CDBs)?",
        choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True, initial='no'
    )
    total_investment_value = forms.DecimalField(
        label="Qual o valor total aproximado desses investimentos? (R$)",
        max_digits=15, decimal_places=2, min_value=Decimal('0.01'), required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': 'Ex.: 500.000,00'})
    )
    receives_rent = forms.ChoiceField(
        label="Você recebe aluguéis de imóveis?", choices=[('no', 'Não'), ('yes', 'Sim')],
        widget=forms.RadioSelect, required=True, initial='no'
    )
    monthly_rent = forms.DecimalField(
        label="Qual o valor mensal total recebido de aluguéis? (R$)", max_digits=15, decimal_places=2, min_value=Decimal('0.01'), required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': 'Ex.: 5.000,00'}),
        help_text="Informe o valor líquido recebido, antes de impostos."
    )
    number_of_heirs = forms.IntegerField(
        label="Quantas pessoas seriam suas herdeiras (filhos, cônjuge, etc.)?", min_value=0, required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control-simulacao', 'placeholder': 'Ex.: 3'}),
        help_text="Inclua todas as pessoas que herdariam seus bens, como filhos, cônjuge ou outros."
    )

    def clean(self):
        cleaned_data = super().clean()
        number_of_properties = cleaned_data.get('number_of_properties')
        total_property_value = cleaned_data.get('total_property_value')
        property_state = cleaned_data.get('property_state')
        has_companies = cleaned_data.get('has_companies')
        number_of_companies = cleaned_data.get('number_of_companies')
        company_tax_regime = cleaned_data.get('company_tax_regime')
        monthly_profit = cleaned_data.get('monthly_profit')
        has_investments = cleaned_data.get('has_investments')
        total_investment_value = cleaned_data.get('total_investment_value')
        receives_rent = cleaned_data.get('receives_rent')
        monthly_rent = cleaned_data.get('monthly_rent')

        if number_of_properties is not None and number_of_properties > 0:
            if not total_property_value or total_property_value <= 0:
                self.add_error('total_property_value', "Com imóveis, o valor estimado deve ser informado e maior que zero.")
            if not property_state:
                self.add_error('property_state', "Se possui imóveis, informe o estado principal.")
        else:
            cleaned_data['total_property_value'] = Decimal('0')
            cleaned_data['property_state'] = ''

        if has_companies == 'yes':
            if number_of_companies is None or number_of_companies <= 0:
                self.add_error('number_of_companies', "Se possui empresas, informe a quantidade.")
            if not company_tax_regime:
                self.add_error('company_tax_regime', "Se possui empresas, informe o tipo de tributação.")
            if monthly_profit is None:
                self.add_error('monthly_profit', "Se possui empresas, informe o lucro mensal (pode ser 0).")
            elif monthly_profit < 0:
                self.add_error('monthly_profit', "O lucro mensal não pode ser negativo.")
        else:
            cleaned_data['number_of_companies'] = 0
            cleaned_data['company_tax_regime'] = ''
            cleaned_data['monthly_profit'] = Decimal('0')

        if has_investments == 'yes' and (not total_investment_value or total_investment_value <= 0):
            self.add_error('total_investment_value', "Se possui investimentos, informe o valor total.")
        elif has_investments == 'no':
            cleaned_data['total_investment_value'] = Decimal('0')

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

class ChatMessageForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Digite sua mensagem aqui...',
            'class': 'chat-input-textarea form-control-custom' # Add relevant classes
        }),
        label="" # No explicit label shown, placeholder is descriptive
    )

    class Meta:
        model = ChatMessage
        fields = ['content']

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

class PastaDocumentoForm(forms.ModelForm):
    class Meta:
        model = PastaDocumento
        fields = ['nome', 'parent_folder']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control-custom', 'placeholder': 'Nome da Nova Pasta'}),
            'parent_folder': forms.Select(attrs={'class': 'form-control-custom'}),
        }
        labels = {
            'nome': 'Nome da Pasta',
            'parent_folder': 'Salvar Dentro De (Opcional)'
        }

    def __init__(self, *args, **kwargs):
        processo_holding_instance = kwargs.pop('processo_holding', None)
        # You might want to exclude the current folder if editing, to prevent self-parenting
        # current_folder_instance = kwargs.pop('current_folder', None) 
        super().__init__(*args, **kwargs)
        
        if processo_holding_instance:
            queryset = PastaDocumento.objects.filter(processo_holding=processo_holding_instance)
            # if current_folder_instance: # Logic for editing to prevent self-parenting or circular deps
            #     queryset = queryset.exclude(pk=current_folder_instance.pk)
            #     # Also exclude descendants of current_folder_instance if it's an edit form
            self.fields['parent_folder'].queryset = queryset.order_by('nome')
            self.fields['parent_folder'].required = False
            self.fields['parent_folder'].empty_label = "--- Raiz do Processo (Nenhuma Pasta Pai) ---"
        else:
            self.fields['parent_folder'].queryset = PastaDocumento.objects.none()
            self.fields['parent_folder'].widget.attrs['disabled'] = True
            self.fields['parent_folder'].required = False
            self.fields['parent_folder'].empty_label = "--- (Processo não definido) ---"
    
    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        # Basic validation for folder name, e.g., no slashes
        if '/' in nome or '\\' in nome:
            raise ValidationError("Nome da pasta não pode conter barras ('/' ou '\\').")
        return nome
    
    def clean(self):
        cleaned_data = super().clean()
        parent_folder = cleaned_data.get('parent_folder')
        # If editing an existing folder (self.instance.pk is not None),
        # prevent making it a child of itself or its own descendants.
        # This logic is more complex and can be added if editing folders is implemented.
        # For creation, unique_together in the model handles duplicates at the same level.
        return cleaned_data

class DocumentUploadForm(forms.ModelForm):
    pasta = forms.ModelChoiceField(
        queryset=PastaDocumento.objects.none(),
        required=False,
        label="Salvar na Pasta (Opcional)",
        widget=forms.Select(attrs={'class': 'form-control-custom'})
    )

    class Meta:
        model = Documento
        fields = ['nome_documento_logico', 'pasta', 'arquivo', 'categoria', 'descricao_adicional']
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
        # ***** THIS IS THE CRUCIAL FIX: POP 'processo_holding' BEFORE SUPER() *****
        processo_holding_instance = kwargs.pop('processo_holding', None)
        # ***********************************************************************
        super().__init__(*args, **kwargs) # Now kwargs doesn't contain 'processo_holding'
        
        self.fields['arquivo'].widget.attrs.update({'lang': 'pt-br'})

        if processo_holding_instance:
            self.fields['pasta'].queryset = PastaDocumento.objects.filter(processo_holding=processo_holding_instance).order_by('nome')
            self.fields['pasta'].empty_label = "--- Raiz do Processo (Nenhuma Pasta) ---"
        else:
            self.fields['pasta'].widget.attrs['disabled'] = True
            self.fields['pasta'].empty_label = "--- (Processo não definido para pastas) ---"



class ManagementDocumentUploadForm(forms.ModelForm):
    pasta = forms.ModelChoiceField(
        queryset=PastaDocumento.objects.none(),
        required=False,
        label="Salvar na Pasta (Opcional)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Documento
        fields = ['nome_documento_logico', 'pasta', 'arquivo', 'categoria', 'descricao_adicional']
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
        # ***** THIS IS THE CRUCIAL FIX: POP 'processo_holding' BEFORE SUPER() *****
        processo_holding_instance = kwargs.pop('processo_holding', None)
        # ***********************************************************************
        super().__init__(*args, **kwargs) # Now kwargs doesn't contain 'processo_holding'

        self.fields['arquivo'].widget.attrs.update({'lang': 'pt-br'})

        if processo_holding_instance:
            self.fields['pasta'].queryset = PastaDocumento.objects.filter(processo_holding=processo_holding_instance).order_by('nome')
            self.fields['pasta'].empty_label = "--- Raiz do Processo (Nenhuma Pasta) ---"
        else:
            self.fields['pasta'].widget.attrs['disabled'] = True
            self.fields['pasta'].empty_label = "--- (Processo não definido para pastas) ---"
