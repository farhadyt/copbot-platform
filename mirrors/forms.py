from django import forms
from .models import Mirror, Target, TradingPlatform, ConnectedWallet, TradingBot

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

class ConnectedWalletForm(forms.ModelForm):
    """Form for connecting a trading wallet"""
    platform = forms.ModelChoiceField(
        queryset=TradingPlatform.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control glow-input',
            'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
        })
    )
    
    class Meta:
        model = ConnectedWallet
        fields = ['address', 'private_key_encrypted', 'platform']
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Enter wallet address...',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'private_key_encrypted': forms.PasswordInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Enter private key (will be encrypted)...',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
        }


class TradingBotForm(forms.ModelForm):
    """Form for configuring trading bot"""
    class Meta:
        model = TradingBot
        fields = [
            'wallet', 'platform', 'copy_mode', 
            'max_trade_size', 'min_trade_size', 'daily_loss_limit',
            'take_profit_percentage', 'stop_loss_percentage',
            'slippage_tolerance', 'gas_limit_multiplier', 'delay_seconds'
        ]
        widgets = {
            'wallet': forms.Select(attrs={
                'class': 'form-control glow-input',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'platform': forms.Select(attrs={
                'class': 'form-control glow-input',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'copy_mode': forms.Select(attrs={
                'class': 'form-control glow-input',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'max_trade_size': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Maximum trade size in SOL',
                'step': '0.01',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'min_trade_size': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Minimum trade size in SOL',
                'step': '0.01',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'daily_loss_limit': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Daily loss limit in USD',
                'step': '0.01',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'take_profit_percentage': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Take profit %',
                'step': '0.1',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'stop_loss_percentage': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Stop loss %',
                'step': '0.1',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'slippage_tolerance': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Slippage tolerance %',
                'step': '0.1',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'gas_limit_multiplier': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Gas limit multiplier',
                'step': '0.1',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'delay_seconds': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Delay before copy (seconds)',
                'min': '0',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
        }