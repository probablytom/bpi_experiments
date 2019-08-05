from bpi_13_experimental_frontend import run_model, skip_current_action, manually_log, new_trace
from functools import partial

class ExperimentAdvice(object):
    triggered_counts = {}

    def __init__(self, func_to_run = lambda a,b: None):
        self.already_triggered = False
        self.func_to_run = func_to_run

    def prelude(self, attribute, actor):
        if attribute.func_name not in ExperimentAdvice.triggered_counts.keys():
            ExperimentAdvice.triggered_counts[attribute.func_name] = 0

        lowest_triggered_count = sorted(ExperimentAdvice.triggered_counts.items(), key=lambda i: i[1])[0][1]

        if not self.already_triggered and ExperimentAdvice.triggered_counts[attribute.func_name] == lowest_triggered_count:
            self.func_to_run(attribute, actor)
            ExperimentAdvice.triggered_counts[attribute.func_name] += 1
            self.already_triggered = True


SkippingAdvice = partial(ExperimentAdvice, lambda a,b: skip_current_action())
RepeatingAdvice = partial(ExperimentAdvice, manually_log)

### === experiments run below

run_model(SkippingAdvice,
          num_ticks=100,
          num_start_messages=1,
          outputfile='playground_out.xes')


