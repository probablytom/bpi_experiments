from bpi_13_experimental_frontend import run_model, skip_current_action, manually_log, new_trace, generate_XES
from bpi_13_experimental_frontend import CustomerServiceWorkflow, action_log
import bpi_13_experimental_frontend
from functools import partial

class ExperimentAdvice(object):
    triggered_counts = dict()

    @classmethod
    def reset_experimental_record(cls):
        ExperimentAdvice.triggered_counts = dict()

    def __init__(self, func_to_run = lambda a,b: None, times_to_trigger=1):
        self.triggers_remaining = times_to_trigger
        self.func_to_run = func_to_run

    def encore(self, attribute, actor, _result):
        if attribute.func_name not in ExperimentAdvice.triggered_counts.keys():
            ExperimentAdvice.triggered_counts[attribute.func_name] = 0

        lowest_triggered_count = sorted(ExperimentAdvice.triggered_counts.items(), key=lambda i: i[1])[0][1]

        if self.triggers_remaining > 0 \
                and ExperimentAdvice.triggered_counts[attribute.func_name] <= lowest_triggered_count\
                and attribute.func_name != 'START'\
                and attribute.func_name != 'END':
            self.func_to_run(attribute, actor)
            ExperimentAdvice.triggered_counts[attribute.func_name] += 1
            self.triggers_remaining -= 1


        # If necessary, erase history
        if attribute.func_name == "END" \
                and self.triggers_remaining > 0:
            action_log.pop()



def remove_previous_action(_, __):
    action_log[-1].pop()

SkippingAdvice = partial(ExperimentAdvice, remove_previous_action)
RepeatingAdvice = partial(ExperimentAdvice, manually_log)


# while len(HackedTogetherLog.total_log) < 5:
#     run_model(FuzzerClass=SkippingAdvice,
#               num_ticks=200,
#               num_start_messages=1,
#               outputfile='mattia_sample.xes')
#     new_trace()
#
# while len(action_log) < 20:
#     if action_log[-1] != []:
#         new_trace()
#     run_model(FuzzerClass=RepeatingAdvice,
#               num_ticks=200,
#               num_start_messages=1,
#               outputfile='sample_repeating_20.xes')
#
# record = "".join([(repeated_func + "\n") * count for repeated_func, count in ExperimentAdvice.triggered_counts.items()])
#
# with open('sample_repeating_20_repeated_actions.txt', 'w') as record_of_repeated_funcs:
#     record_of_repeated_funcs.write(record)


ExperimentAdvice.reset_experimental_record()
bpi_13_experimental_frontend.action_log = []


while len(action_log) < 20:
    new_trace()
    run_model(FuzzerClass=SkippingAdvice,
              num_ticks=200,
              num_start_messages=1,
              outputfile='sample_skipping_20.xes')

record = "".join([(skipped_func + "\n") * count for skipped_func, count in ExperimentAdvice.triggered_counts.items()])

with open('sample_skipping_20_skipped_actions.txt', 'w') as record_of_skipped_funcs:
    record_of_skipped_funcs.write(record)

#
# for i in range(50):
#     run_model(FuzzerClass=ExperimentAdvice,   # Defaults to identity
#               num_ticks=200,
#               num_start_messages=1,
#               outputfile='mattia_sample.xes')
#
#
# generate_XES(HackedTogetherLog.total_log, '20_repeating_tasks.xes')
pass