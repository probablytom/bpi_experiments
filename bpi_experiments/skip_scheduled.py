from bpi_13_experimental_frontend import run_model, skip_current_action

class SkipLogAdvice(object):

    def should_skip(self, attr):
        '''
        Skip all scheduling actions.
        :return:  Bool indicating whether to activate.
        '''
        return 'schedule' in attr.func_name

    def prelude(self, attr, _):
        if self.should_skip(attr):
            skip_current_action()

run_model(SkipLogAdvice,
          num_ticks=100,
          num_start_messages=1)

