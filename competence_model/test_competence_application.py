import unittest
from bpi_13_experimental_frontend import run_model_advanced_aspect_application as run_model
from bpi_13_experimental_frontend import construct_universe, action_log, generate_CSV, generate_XES
from bpi_13_experimental_frontend import reset_universe, new_trace, experimental_environment
from competence import CompetenceModel, ExperimentAdvice, NewTasksOnEnd

att = 0.7
intro = 0.5

class TestCompetence(unittest.TestCase):
    def test_competence_application(self):
        construct_universe()
        run_model([(CompetenceModel, 'get_next_task', list(), dict())],
                  num_start_messages=1,
                  num_ticks=150)

    def test_mistake_hooks(self):

        construct_universe()
        num_traces_to_make = 5
        while not num_traces_to_make == ExperimentAdvice.invoked_count:

            run_model(([
                (ExperimentAdvice, 'all actors', list(), dict()),
                (CompetenceModel, 'get_next_task', list(), dict()),
            ]),
                num_start_messages=1,
                num_ticks=100)

            if not ExperimentAdvice.invoked:
                action_log.pop()
                if 'fuzzed tasks' in experimental_environment.keys() and experimental_environment['fuzzed tasks'][-1] == []:
                    experimental_environment['fuzzed tasks'].pop()
            new_trace()
            reset_universe()

        # We have one too many traces, so we have to delete the one made by the last new_trace call.
        action_log.pop()

        generate_XES()
        generate_CSV()

    def test_multiple_traces_consistent_actors(self):

        construct_universe()
        ticks = 350
        run_model(([
            # (ActAbovePermissions, 'get_next_task', list(), dict()),
            (CompetenceModel, 'get_next_task', [0.05, ticks/2], dict()),
            (ExperimentAdvice, 'all workflows', list(), dict()),
            (NewTasksOnEnd, 'end', list(), dict()),
        ]),
            num_start_messages=1,
            num_ticks=ticks,
        )

        # We also stopped halfway through a simulation...so unless the last action in the last action log is one the simulation should end on, we should remove that trace (and its fuzzing effects)
        if action_log[-1][-1] != "A_declined" \
            and action_log[-1][-1] != "W_beoordelen_fraude_complete" \
            and action_log[-1][-1] != "W_wijzigen_contractgegevens_schedule":
            action_log.pop()
            if len(experimental_environment["fuzzed tasks"]) != len(action_log):
                experimental_environment["fuzzed tasks"].pop()

        generate_XES()
        generate_CSV()

if __name__ == '__main__':
    unittest.main()
