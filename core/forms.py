from django import forms
from .models import Holding, ProcessoHolding

class HoldingForm(forms.ModelForm):
    class Meta:
        model = Holding
        fields = [
            'nome_holding', 'descricao', 'primary_goal', 'asset_types', 'industry_focus',
            'jurisdiction', 'valor_patrimonio_integralizado', 'legal_structure', 'subsidiaries',
            'update_frequency', 'milestones'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'asset_types': forms.Textarea(attrs={'rows': 3}),
            'subsidiaries': forms.Textarea(attrs={'rows': 3}),
            'milestones': forms.Textarea(attrs={'rows': 3}),
        }