from adjallocation.hungarian import HungarianAllocator
from draw.models import Debate
from utils.management.base import RoundCommand, CommandError
from results.dbutils import add_ballotsets_to_round
from results.management.commands.generateresults import GenerateResultsCommandMixin, SUBMITTER_TYPE_MAP
from tournaments.models import Round

from django.contrib.auth import get_user_model

User = get_user_model()

class Command(GenerateResultsCommandMixin, RoundCommand):

    help = "Adds draws and results to the database"
    confirm_round_destruction = "delete ALL DEBATES"

    def handle_round(self, round, **options):
        self.stdout.write("Deleting all debates in round '{}'...".format(round.name))
        Debate.objects.filter(round=round).delete()
        round.draw_status = Round.STATUS_NONE
        round.save()

        self.stdout.write("Checking in all teams, adjudicators and venues for round '{}'...".format(round.name))
        round.activate_all()

        self.stdout.write("Generating a draw for round '{}'...".format(round.name))
        round.draw()
        round.draw_status = Round.STATUS_CONFIRMED
        round.save()

        self.stdout.write("Auto-allocating adjudicators for round '{}'...".format(round.name))
        round.allocate_adjudicators(HungarianAllocator)

        self.stdout.write("Generating results for round '{}'...".format(round.name))
        add_ballotsets_to_round(round, **self.ballotset_kwargs(options))

        round.tournament.current_round = round
        round.tournament.save()
