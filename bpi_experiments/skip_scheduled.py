from bpi_13_experimental_frontend import run_model, skip_current_action

class SkipLogAdvice(object):
    def prelude(self, attr, _):
        if 'schedule' in attr.func_name:
            skip_current_action()

run_model(SkipLogAdvice,
          num_ticks=100,
          num_start_messages=1)

