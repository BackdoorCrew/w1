from django import forms
from .models import Holding
import json

class HoldingForm(forms.ModelForm):
    # Rental properties (dynamic fields)
    rental_properties = forms.CharField(widget=forms.HiddenInput(), required=False)
    # Companies (dynamic fields)
    companies = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Holding
        fields = [
            'nome_holding', 'has_successors', 'successor_count', 'successor_age_range',
            'has_existing_plan', 'has_rental_income', 'rental_property_count', 'rental_details',
            'has_companies', 'company_count', 'company_details', 'has_protection_concerns',
            'has_litigation_risk', 'protected_assets', 'irpf_bracket', 'has_dividends',
            'dividend_amount', 'update_frequency'
        ]
        widgets = {
            'rental_details': forms.HiddenInput(),
            'company_details': forms.HiddenInput(),
            'protected_assets': forms.Textarea(attrs={'rows': 3}),
            'dividend_amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Parse and validate rental_properties JSON
        if cleaned_data.get('has_rental_income') and cleaned_data.get('rental_properties'):
            try:
                rental_data = json.loads(cleaned_data['rental_properties'])
                cleaned_data['rental_details'] = json.dumps(rental_data)
                cleaned_data['rental_property_count'] = len(rental_data)
            except json.JSONDecodeError:
                self.add_error('rental_properties', 'Dados de imóveis inválidos.')
        # Parse and validate companies JSON
        if cleaned_data.get('has_companies') and cleaned_data.get('companies'):
            try:
                company_data = json.loads(cleaned_data['companies'])
                cleaned_data['company_details'] = json.dumps(company_data)
                cleaned_data['company_count'] = len(company_data)
            except json.JSONDecodeError:
                self.add_error('companies', 'Dados de empresas inválidos.')
        return cleaned_data