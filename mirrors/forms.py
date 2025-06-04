from django import forms
from .models import Mirror, Target

class MirrorForm(forms.ModelForm):
    class Meta:
        model = Mirror
        fields = ['codename', 'mirror_type', 'max_echo_size', 'risk_threshold', 'gain_target']
        widgets = {
            'codename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unique codename...'
            }),
            'mirror_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'max_echo_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Max trade size (SOL)'
            }),
            'risk_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stop loss %'
            }),
            'gain_target': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Take profit %'
            })
        }

class TargetForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = ['beacon_id', 'alias']
        widgets = {
            'beacon_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wallet address to track...'
            }),
            'alias': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nickname (optional)'
            })
        }