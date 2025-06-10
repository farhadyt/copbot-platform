from django import forms
from .models import Mirror, Target, TradingPlatform, ConnectedWallet, TradingBot, Agent

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

class AgentForm(forms.ModelForm):
    """Form for creating and editing Shadow agents"""
    
    # Active days as checkboxes
    active_days = forms.MultipleChoiceField(
        choices=[
            (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
            (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        initial=[0, 1, 2, 3, 4, 5, 6]  # All days selected by default
    )
    
    # Scan frequency with proper choices
    scan_frequency = forms.ChoiceField(
        choices=[
            ('Maximum Fast', 'Maximum Fast - Highest Speed'),
            ('Fast', 'Fast - High Speed'),
            ('Normal', 'Normal - Medium Speed'),
            ('Slow', 'Slow - Low Speed')
        ],
        initial='Maximum Fast',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control glow-input',
            'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
        })
    )
    
    class Meta:
        model = Agent
        fields = [
            'name', 'agent_type', 'active_days', 'active_hours_start', 'active_hours_end',
            'max_transactions_hour', 'max_transactions_day', 'scan_frequency',
            'min_transaction_value', 'max_transaction_value', 'min_wallet_balance',
            'token_filter_type', 'excluded_tokens', 'included_tokens', 'max_retention_days'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Leave empty for auto-generation (e.g., Shadow-1)',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;',
                'required': False
            }),
            'agent_type': forms.HiddenInput(),  # Will be set in the view
            'active_hours_start': forms.TimeInput(attrs={
                'class': 'form-control glow-input',
                'type': 'time',
                'value': '00:00',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'active_hours_end': forms.TimeInput(attrs={
                'class': 'form-control glow-input',
                'type': 'time',
                'value': '23:59',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'max_transactions_hour': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Max transactions per hour (optional)',
                'min': '1',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'max_transactions_day': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Max transactions per day (optional)',
                'min': '1',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'min_transaction_value': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Minimum transaction value (USD)',
                'step': '0.01',
                'value': '1.00',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'max_transaction_value': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Maximum transaction value (USD, optional)',
                'step': '0.01',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'min_wallet_balance': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Minimum wallet balance (USD, optional)',
                'step': '0.01',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'token_filter_type': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'excluded_tokens': forms.Textarea(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Enter token symbols separated by commas (e.g., SCAM, RISKY)',
                'rows': 3,
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'included_tokens': forms.Textarea(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Enter token symbols separated by commas (e.g., SOL, BONK, WIF)',
                'rows': 3,
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
            'max_retention_days': forms.NumberInput(attrs={
                'class': 'form-control glow-input',
                'placeholder': 'Max days to keep transaction data',
                'min': '1',
                'value': '10',
                'style': 'background: rgba(0, 10, 20, 0.8); border: 1px solid var(--primary); color: #fff;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make name field not required
        self.fields['name'].required = False
        
        # Convert active_days from list to comma-separated string for form processing
        if self.instance and self.instance.pk and self.instance.active_days:
            if isinstance(self.instance.active_days, list):
                self.initial['active_days'] = self.instance.active_days
    
    def clean_name(self):
        """Allow empty name for auto-generation"""
        name = self.cleaned_data.get('name')
        if name:
            return name.strip()
        return ''
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Convert active_days from form data to list
        active_days_data = self.cleaned_data.get('active_days', [])
        if active_days_data:
            instance.active_days = [int(day) for day in active_days_data]
        else:
            instance.active_days = []
        
        if commit:
            instance.save()
        
        return instance