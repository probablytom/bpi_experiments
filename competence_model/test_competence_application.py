import unittest
from bpi_13_experimental_frontend import run_model_advanced_aspect_application as run_model
from bpi_13_experimental_frontend import construct_universe, action_log, generate_CSV, generate_XES
from bpi_13_experimental_frontend import reset_universe, new_trace, experimental_environment, reset_traces
import bpi_13_experimental_frontend
from competence import CompetenceModel, ExperimentAdvice, NewTasksOnEnd
from functools import partial
from Queue import Queue

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
        iterations = 5
        simulate = partial(run_model,
                           ([
                               # (ActAbovePermissions, 'get_next_task', list(), dict()),
                               (CompetenceModel, 'get_next_task', [0.05*iterations, ticks/2/iterations], dict()),
                               (ExperimentAdvice, 'all workflows', list(), dict()),
                               (NewTasksOnEnd, 'end', list(), dict()),
                           ]),
                           num_start_messages=1,
                           num_ticks=ticks
                           )
        # run_model(([
        #     # (ActAbovePermissions, 'get_next_task', list(), dict()),
        #     (CompetenceModel, 'get_next_task', [0.05*iterations, ticks/2/iterations], dict()),
        #     (ExperimentAdvice, 'all workflows', list(), dict()),
        #     (NewTasksOnEnd, 'end', list(), dict()),
        # ]),
        #     num_start_messages=1,
        #     num_ticks=ticks,
        # )

        self.play_simulation(simulate, discard_work=True)
        self.play_simulation(simulate, discard_work=False)

        # We also stopped halfway through a simulation...so unless the last action in the last action log is one the simulation should end on, we should remove that trace (and its fuzzing effects)
        try:
            if action_log[-1][-1] != "A_declined" \
                and action_log[-1][-1] != "W_beoordelen_fraude_complete" \
                and action_log[-1][-1] != "W_wijzigen_contractgegevens_schedule":
                action_log.pop()
                if len(experimental_environment["fuzzed tasks"]) != len(action_log):
                    experimental_environment["fuzzed tasks"].pop()
        except:
            pass

        generate_XES()
        generate_CSV()

    def play_simulation(self, simulation_function, discard_work=True, *args, **kwargs):
        '''
        Runs through the simulation but discards the results of the work
        (so no activity is recorded, but the actors learn, retire, etc.)
        :param discard_work: Dictates whether the work done playing through this simulation should be discarded, so actors simply learn.
        :return:
        '''
        simulation_function(*args, **kwargs)
        # reset_traces() if discard_work else None
        if discard_work:
            [bpi_13_experimental_frontend.action_log.pop() for _ in range(len(bpi_13_experimental_frontend.action_log))]
            bpi_13_experimental_frontend.action_log.append([])
            experimental_environment.__delitem__("fuzzed tasks")

            # Remove all pending tasks
            bpi_13_experimental_frontend.company.troupe_work_queue = Queue()
            bpi_13_experimental_frontend.reps.troupe_work_queue = Queue()
            bpi_13_experimental_frontend.specialists.troupe_work_queue = Queue()



if __name__ == '__main__':
    unittest.main()
