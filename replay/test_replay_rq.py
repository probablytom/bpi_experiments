import unittest
import xml.etree.ElementTree as ET
from functools import partial
from bpi_13_experimental_frontend import run_model_advanced_aspect_application as run_model
from bpi_13_experimental_frontend import construct_universe, experimental_environment, generate_XES, generate_CSV
from bpi_13_experimental_frontend import action_log
from competence_model.competence import CompetenceModel, ExperimentAdvice, NewTasksOnEnd
from Queue import Queue
from random import choice, randint
from copy import copy
import bpi_13_experimental_frontend



class MyTestCase(unittest.TestCase):

    def test_replay_data_generation(self):
        construct_universe()
        ticks = 50000
        min_dataset_required = 1000  # We want at least 1000 traces.
        iterations = 1


        class MonteCarlo:
            traces = []

            class Governor:
                def encore(self, _attribute, _actor, _res):
                    MonteCarlo.traces.append(list())

            class Collector:
                def encore(self, attribute, _actor, _res):
                    MonteCarlo.traces[-1].append(attribute.func_name)


        simulate = partial(run_model,
                           ([
                               # (ActAbovePermissions, 'get_next_task', list(), dict()),
                               # (CompetenceModel, 'get_next_task', [0.05*iterations, ticks/2/iterations], dict()),
                               # (ExperimentAdvice, 'all workflows', list(), dict()),
                               (NewTasksOnEnd, 'end', list(), dict()),
                               (MonteCarlo.Governor, 'start', list(), dict()),
                               (MonteCarlo.Collector, 'all workflows', list(), dict()),
                           ]),
                           num_start_messages=1,
                           num_ticks=ticks
                           )


        self.play_simulation(simulate)
        while len(MonteCarlo.traces) < min_dataset_required:
            self.play_simulation(simulate, discard_work=False)
            while [] in MonteCarlo.traces: MonteCarlo.traces.remove([])
            try:
                if MonteCarlo.traces[-1][-1] != "A_declined" \
                        and MonteCarlo.traces[-1][-1] != "W_beoordelen_fraude_complete" \
                        and MonteCarlo.traces[-1][-1] != "W_wijzigen_contractgegevens_schedule":
                    MonteCarlo.traces.pop()
            except:
                pass

            print(len(MonteCarlo.traces))


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

        def completes_trace(incomplete, sample):
            inc_position = 0
            for event in sample:
                if event == incomplete[inc_position]:
                    inc_position += 1
                if inc_position == len(incomplete):
                    return True
            return False

        to_complete = copy(choice(MonteCarlo.traces))

        num_gaps = len(to_complete) - 3
        for _ in range(num_gaps):
            to_complete.remove(choice(to_complete))

        completes_sample = partial(completes_trace, to_complete)

        MonteCarlo.traces = map(tuple, MonteCarlo.traces)

        histogram = {trace: MonteCarlo.traces.count(trace) for trace in MonteCarlo.traces if completes_sample(trace)}

        lim = randint(0, sum(histogram.values()))
        total = 0
        for completing_trace, count in histogram.items():
            total += count
            if total > lim:
                break

        print("We complete the trace: \n\t" + str(to_complete) + "\n...with the trace...\n\t" + str(completing_trace))

        # generate_XES()
        # generate_CSV()

    def test_parsing_traces(self):
        tree = ET.parse('log.xes')
        root = tree.getroot()
        traces = [child for child in root if len(child.tag) > 5 and child.tag[-5:] == 'trace']
        print(traces)
        event_log = []
        for trace in traces:
            event_log.append([])
            for event in trace[1:]:  # We skip the int at the beginning of them
                event_log[-1].append(event._children[0].attrib['value'])

        print(event_log)



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
