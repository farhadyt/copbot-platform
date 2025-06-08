from django.core.management.base import BaseCommand
from mirrors.models import TradingPlatform


class Command(BaseCommand):
    help = 'Initialize trading platforms'

    def handle(self, *args, **options):
        platforms = [
            {
                'name': 'Raydium',
                'api_endpoint': 'https://api.raydium.io/v2',
            },
            {
                'name': 'Jupiter',
                'api_endpoint': 'https://price.jup.ag/v4',
            },
            {
                'name': 'Pump',
                'api_endpoint': 'https://api.pump.fun',
            },
            {
                'name': 'Orca',
                'api_endpoint': 'https://api.orca.so',
            },
            {
                'name': 'DexScreener',
                'api_endpoint': 'https://api.dexscreener.com',
            },
            {
                'name': 'Photon',
                'api_endpoint': 'https://api.photon.trade',
            },
            {
                'name': 'GMGN',
                'api_endpoint': 'https://api.gmgn.ai',
            },
        ]
        
        created_count = 0
        for platform_data in platforms:
            platform, created = TradingPlatform.objects.get_or_create(
                name=platform_data['name'],
                defaults={
                    'api_endpoint': platform_data['api_endpoint'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created platform: {platform.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Platform already exists: {platform.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal platforms created: {created_count}')
        ) 