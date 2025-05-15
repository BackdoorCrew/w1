from django import forms
from .models import Holding

class HoldingForm(forms.ModelForm):
    ASSET_TYPE_CHOICES = [
        ('imoveis', 'Imóveis'),
        ('empresas', 'Empresas'),
        ('investimentos', 'Investimentos'),
        ('dinheiro', 'Dinheiro em conta'),
    ]
    IMPORTANT_INFO_CHOICES = [
        ('progresso', 'Progresso do processo'),
        ('documentos', 'Documentos necessários'),
        ('beneficios', 'Benefícios financeiros'),
    ]

    asset_types = forms.MultipleChoiceField(choices=ASSET_TYPE_CHOICES, widget=forms.CheckboxSelectMultiple, required=False)
    important_info = forms.MultipleChoiceField(choices=IMPORTANT_INFO_CHOICES, widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = Holding
        fields = [
            'nome_holding', 'has_successors', 'successor_names', 'partner_count', 'partner_names',
            'asset_types', 'valor_patrimonio_integralizado', 'main_goal', 'has_subsidiaries',
            'subsidiary_names', 'timeline', 'has_advisors', 'advisor_info', 'update_frequency',
            'important_info'
        ]
        widgets = {
            'successor_names': forms.Textarea(attrs={'rows': 3}),
            'partner_names': forms.Textarea(attrs={'rows': 3}),
            'subsidiary_names': forms.Textarea(attrs={'rows': 3}),
            'advisor_info': forms.Textarea(attrs={'rows': 3}),
            'valor_patrimonio_integralizado': forms.NumberInput(attrs={'step': '0.01'}),
        }