from django.core.management.base import BaseCommand
from django.utils import timezone
from mirrors.models import Agent
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleanup old transactions based on agent retention policies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--agent-id',
            type=int,
            help='Cleanup transactions for specific agent only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        agent_id = options.get('agent_id')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No actual deletions will occur')
            )
        
        # Get agents with retention policies
        agents_query = Agent.objects.filter(
            agent_type='shadow',
            max_retention_days__isnull=False,
            max_retention_days__gt=0
        )
        
        if agent_id:
            agents_query = agents_query.filter(id=agent_id)
        
        agents = agents_query.all()
        
        if not agents:
            self.stdout.write(
                self.style.WARNING('No agents found with retention policies')
            )
            return
        
        total_deleted = 0
        
        for agent in agents:
            self.stdout.write(f'\nProcessing agent: {agent.name}')
            
            if dry_run:
                # Count what would be deleted
                from django.utils import timezone
                from datetime import timedelta
                
                cutoff_date = timezone.now() - timedelta(days=agent.max_retention_days)
                old_count = agent.transactions.filter(timestamp__lt=cutoff_date).count()
                
                if old_count > 0:
                    self.stdout.write(
                        f'  Would delete {old_count} transactions older than {agent.max_retention_days} days'
                    )
                else:
                    self.stdout.write('  No old transactions to delete')
            else:
                # Actually delete old transactions
                deleted_count = agent.clean_old_transactions()
                
                if deleted_count > 0:
                    total_deleted += deleted_count
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Deleted {deleted_count} old transactions'
                        )
                    )
                else:
                    self.stdout.write('  No old transactions to delete')
        
        if not dry_run and total_deleted > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nTotal transactions deleted: {total_deleted}'
                )
            )
        elif not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\nNo transactions needed cleanup')
            )
        
        # Show summary statistics
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY STATISTICS:')
        self.stdout.write('='*50)
        
        for agent in agents:
            stats = agent.get_transaction_stats()
            self.stdout.write(f'\nAgent: {agent.name}')
            self.stdout.write(f'  Total transactions: {stats["total_transactions"]}')
            self.stdout.write(f'  Total trades: {stats["total_trades"]}')
            self.stdout.write(f'  Win rate: {stats["win_rate"]}%')
            self.stdout.write(f'  Total profit: ${stats["total_profit"]:.2f}')
            self.stdout.write(f'  Retention policy: {agent.max_retention_days} days') 