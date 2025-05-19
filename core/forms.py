from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from core.models import User, Holding

class CustomSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')

    class Meta(UserCreationForm.Meta): # Herda do Meta do UserCreationForm
        model = User # Agora se refere a core.models.User
        # Se seu UserCreationForm precisa de 'email' explicitamente no fields aqui,
        # e seu core.User não tem 'username', ajuste os fields.
        # Por exemplo, se email é o USERNAME_FIELD:
        fields = ('email', 'first_name') # Adicione 'last_name' se o tiver como campo separado

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Se estiver editando, permita o mesmo email
        if self.instance and self.instance.pk and self.instance.email == email:
            return email
        if User.objects.filter(email=email).exists(): # User é core.models.User
            raise ValidationError("Este email já está em uso.")
        return email

class HoldingForm(forms.Form):
    company_name = forms.CharField(max_length=100, required=True, label="Nome da Empresa/Holding")
    owner_name = forms.CharField(max_length=100, required=True, label="Nome do Proprietário Principal")
    email = forms.EmailField(required=True, label="Email de Contato")
    phone = forms.CharField(max_length=15, required=True, label="Telefone de Contato")
    number_of_properties = forms.IntegerField(min_value=0, required=True, label="Número de Imóveis")
    number_of_companies = forms.IntegerField(min_value=0, required=True, label="Número de Outras Empresas")
    message = forms.CharField(widget=forms.Textarea, required=False, label="Mensagem Adicional")

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
    
class ConsultantCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmar Senha")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email'] # Adicione outros campos se necessário

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este email já está em uso.")
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
        user.is_staff = False # Decida se consultores devem ter acesso ao admin do Django
        user.is_active = True
        if commit:
            user.save()
        return user
    
class AssignConsultantToHoldingForm(forms.ModelForm):
    consultor_responsavel = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='consultor', is_active=True),
        required=False, # Torne obrigatório se necessário
        label="Consultor Responsável",
        empty_label="Nenhum (Remover Consultor)"
    )
    # Se você também atribui consultor a ProcessoHolding:
    # consultor_designado_processo = forms.ModelChoiceField(
    #     queryset=User.objects.filter(user_type='consultor', is_active=True),
    #     required=False,
    #     label="Consultor Designado para o Processo"
    # )

    class Meta:
        model = Holding
        fields = ['consultor_responsavel'] # Adicione aqui os campos da Holding que quer editar
        # Se for para ProcessoHolding, mude o model e os fields

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Se você tiver um ProcessoHolding associado à Holding e quiser editar o consultor_designado
    #     if self.instance and hasattr(self.instance, 'processo_criacao') and self.instance.processo_criacao:
    #         self.fields['consultor_designado_processo'].initial = self.instance.processo_criacao.consultor_designado

    # def save(self, commit=True):
    #     holding = super().save(commit)
    #     # Se você tiver um ProcessoHolding e um campo para seu consultor
    #     if hasattr(holding, 'processo_criacao') and holding.processo_criacao:
    #         processo = holding.processo_criacao
    #         processo.consultor_designado = self.cleaned_data.get('consultor_designado_processo')
    #         if commit:
    #             processo.save()
    #     return holding
class HoldingCreationUserForm(forms.ModelForm):
    class Meta:
        model = Holding
        fields = [
            'nome_holding', 'description',
            'has_bank_savings', 'bank_savings_amount',
            'has_heirs', 'heir_count', 'has_succession_plan', 'has_paid_inventory',
            'has_rental_properties', 'rental_property_count', 'rental_income_monthly', 'rental_expenses_monthly',
            'has_litigation_concerns', 'has_legal_issues', 'wants_asset_protection', 'protected_assets',
            'has_companies', 'company_count', 'company_profit_annual', 'distributes_profits',
            'has_multiple_assets', 'wants_efficient_management', 'has_management_difficulties'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'protected_assets': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'nome_holding': 'Nome da Holding que deseja criar',
            # Adicione outros labels conforme necessário para corresponder aos seus templates
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not self.initial.get('nome_holding'):
             self.initial['nome_holding'] = f"{user.first_name} Legacy Holdings" if user.first_name else "Minha Holding Pessoal"
    
class ConsultantCreationForm(forms.ModelForm):
    """
    Formulário para o superusuário criar novas contas de Consultor.
    """
    email = forms.EmailField(
        label="E-mail do Consultor",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'exemplo@dominio.com'})
    )
    first_name = forms.CharField(
        label="Nome",
        max_length=150,
        required=True
    )
    last_name = forms.CharField(
        label="Sobrenome",
        max_length=150,
        required=True
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput,
        help_text="Crie uma senha forte para o consultor."
    )
    confirm_password = forms.CharField(
        label="Confirmar Senha",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User # Usa o seu modelo core.User
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
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
        user = super().save(commit=False) # Não salva no banco ainda
        user.set_password(self.cleaned_data["password"]) # Hashea a senha
        user.user_type = 'consultor' # Define o tipo de usuário
        user.is_staff = False  # Consultores não são staff do admin por padrão
        user.is_active = True # Cria o consultor como ativo
        # is_superuser é False por padrão
        if commit:
            user.save() # Salva o usuário no banco
        return user