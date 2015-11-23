from django.core.management.base import BaseCommand, CommandError
import simulation.views

class Command(BaseCommand):
    args = ''
    help = 'Run normal maintenance on the system'

    def handle(self, *args, **options):
        simulation.views.remove_old_simulations()
        simulation.views.sync_db()