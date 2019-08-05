from bpi_13_experimental_frontend import run_model, manually_log, new_trace, generate_CSV, log_fuzz
from bpi_13_experimental_frontend import action_log, generate_XES, construct_universe, experimental_environment
import bpi_13_experimental_frontend
from functools import partial
from random import choice

class ExperimentAdvice(object):
    triggered_counts = {'A_submitted': 0}
    ignorable_tasks = ['START', 'END']

    def __init__(self, func_to_run, fuzzing_name_label, times_to_trigger=1):
        if times_to_trigger >= min(ExperimentAdvice.triggered_counts.values()):
            self.triggers_remaining = times_to_trigger
        else:
            self.triggers_remaining = min(ExperimentAdvice.triggered_counts.values())

        self.func_to_run = func_to_run
        self.fuzzing_name_label = fuzzing_name_label

        if len(ExperimentAdvice.triggered_counts.items()) > 20:
            self.triggers_remaining += 1
        self.max_triggers = self.triggers_remaining

    def encore(self, attribute, actor, _result):
        if attribute.func_name not in ExperimentAdvice.triggered_counts.keys()\
                and attribute.func_name not in ExperimentAdvice.ignorable_tasks:
            ExperimentAdvice.triggered_counts[attribute.func_name] = 0

        lowest_triggered_count = sorted(ExperimentAdvice.triggered_counts.items(), key=lambda i: i[1])[0][1]

        if self.triggers_remaining > 0 \
                and attribute.func_name not in ExperimentAdvice.ignorable_tasks \
                and ExperimentAdvice.triggered_counts[attribute.func_name] <= lowest_triggered_count:
            self.func_to_run(attribute, actor)

            log_fuzz(self.fuzzing_name_label, attribute.func_name)

            ExperimentAdvice.triggered_counts[attribute.func_name] += 1
            self.triggers_remaining -= 1


        # If necessary, erase history
        if attribute.func_name == "END" \
                and self.triggers_remaining == self.max_triggers:
            action_log.pop()
            experimental_environment['fuzzed tasks'].pop()


class ChangingBehaviour(ExperimentAdvice):
    def __init__(self, func_label_tuples, times_to_trigger=1):
        def select_behaviour(attribute, actor):
            behaviour_function, behaviour_label = choice(func_label_tuples)
            self.fuzzing_name_label = behaviour_label
            return behaviour_function(attribute, actor)
        super(ChangingBehaviour, self).__init__(select_behaviour, "", times_to_trigger)



def remove_previous_action(_, __):
    action_log[-1].pop()

SkippingAdvice = partial(ExperimentAdvice, remove_previous_action, 'skipping')
RepeatingAdvice = partial(ExperimentAdvice, manually_log, 'repeating')
AlternatingBehaviour = partial(ChangingBehaviour, [(remove_previous_action, "skipping"), (manually_log, "repeating")])

bpi_13_experimental_frontend.action_log = []

construct_universe()

while len(action_log) < 25:
    run_model(FuzzerClass=AlternatingBehaviour,
              num_ticks=250,
              num_start_messages=1)
    new_trace()
    print(len(action_log))

action_log.pop()
generate_XES()
generate_CSV()
