import matplotlib.pyplot as plt
from math import exp
from drawer import AdviceBuilder
from bpi_13_experimental_frontend import action_log, log_fuzz, company, new_trace, SpecialistWorkflow, specialists, CustomerServiceActor, set_up_new_actor, SpecialistActor, reps
from functools import partial
from random import random, choice


class ExperimentAdvice(object):

    invoked_count = 0
    invoked = False

    def __init__(self):
        ExperimentAdvice.invoked = False

    def around(self, attribute, actor, *args, **kwargs):
        if actor.mistake_to_make is not None and actor.mistake_to_make[0] == 'before'\
                    and attribute.func_name is not "END" and attribute.func_name is not "START":
            func_to_run = actor.mistake_to_make[1]
            fuzzing_name_label = actor.mistake_to_make[2]
            func_to_run(attribute, actor)

            log_fuzz(fuzzing_name_label, attribute.func_name, actor.actor_name)

            actor.mistake_to_make = None
            ExperimentAdvice.invoked_count += not ExperimentAdvice.invoked  # Increment if it's not been invoked yet.
            ExperimentAdvice.invoked = True

        if actor.mistake_to_make is not None and actor.mistake_to_make[0] == 'around' \
                and attribute.func_name is not "END" and attribute.func_name is not "START":
            func_to_run = actor.mistake_to_make[1]
            fuzzing_name_label = actor.mistake_to_make[2]
            func_to_run(attribute, actor, *args, **kwargs)

            log_fuzz(fuzzing_name_label, attribute.func_name, actor.actor_name)

            actor.mistake_to_make = None
            ExperimentAdvice.invoked_count += not ExperimentAdvice.invoked  # Increment if it's not been invoked yet.
            ExperimentAdvice.invoked = True
        else:
            attribute(*args, **kwargs)

        if actor.mistake_to_make is not None and actor.mistake_to_make[0] == 'after'\
                    and attribute.func_name is not "END" and attribute.func_name is not "START":
            func_to_run = actor.mistake_to_make[1]
            fuzzing_name_label = actor.mistake_to_make[2]
            func_to_run(attribute, actor)

            log_fuzz(fuzzing_name_label, attribute.func_name, actor.actor_name)

            actor.mistake_to_make = None
            ExperimentAdvice.invoked_count += not ExperimentAdvice.invoked  # Increment if it's not been invoked yet.
            ExperimentAdvice.invoked = True


class NewTasksOnEnd(object):

    def encore(self, _attribute, _actor, _result):
        company.recieve_message('start')
        # if not ExperimentAdvice.invoked:
        #     action_log.pop()
        #     if 'fuzzed tasks' in experimental_environment.keys() and experimental_environment['fuzzed tasks'][-1] == []:
        #         experimental_environment['fuzzed tasks'].pop()
        new_trace()
        ExperimentAdvice.invoked = False


def remove_previous_action(_, __):
    action_log[-1].pop()


def repeat_step(_, __):
    action_log[-1].append(action_log[-1][-1])


mistake_points = []


builder = AdviceBuilder()

default_attention = 0.7
default_introspection = 0.5
class CompetenceModel(object):
    show_graphs = True
    def __init__(self, genius=0.1, learning_point=50, *args, **kwargs):
        super(CompetenceModel, self).__init__(*args, **kwargs)
        self.genius = genius
        self.learning_point = learning_point

    def around(self, attribute, actor, *args, **kwargs):
        '''
        To be applied to an Actor's get_next_task.
        :param attribute: An actor's get_next_task implementation
        :param actor: An actor
        :param args:
        :param kwargs:
        :return:
        '''
        # * Prelude to the attribute running
        if not hasattr(actor, 'attentiveness'):
            setattr(actor, 'attentiveness', default_attention)
        if not hasattr(actor, 'introspectiveness'):
            setattr(actor, 'introspectiveness', default_introspection)
        if not hasattr(actor, 'experiences'):
            setattr(actor, 'experiences', list())
        if not hasattr(actor, 'last_mistake_made'):
            setattr(actor, 'last_mistake_made', 0)
        if not hasattr(actor, 'carefulness'):
            setattr(actor, 'carefulness', 10)
        if not hasattr(actor, 'mistake_to_make'):
            setattr(actor, 'mistake_to_make', None)
        if not hasattr(actor, 'number_above_permissions'):
            setattr(actor, 'number_above_permissions', 0)
        if not hasattr(actor, 'retirement_exp'):
            setattr(actor, 'retirement_exp', 2 * self.learning_point - round(random() * self.learning_point * choice([-1,1])) )
        if not hasattr(actor, 'retired'):
            setattr(actor, 'retired', False)

        if sum(actor.experiences) > actor.retirement_exp:

            # When retired, we spawn a replacement actor.
            if not actor.retired:
                actor.retired = True
                # Check to see what kind of actor we need to replace
                isSpecialist = actor.actor_name[0] == 'S'
                if isSpecialist:
                    set_up_new_actor(SpecialistActor, specialists)
                else:
                    set_up_new_actor(CustomerServiceActor, reps)

                # Add to the relevant troupes (and the global clock)!



            return actor.idle


        # If the actor has previously generated a new task, with a
        #  ...cost via `au`, we count the experiences of the task now.
        if hasattr(actor, 'curr_task') and hasattr(actor.curr_task, 'cost'):
            actor.experiences.append(actor.attentiveness * actor.curr_task.cost)
            actor.experiences.append(actor.attentiveness * actor.introspectiveness)


        # Calculations for competence and chance of error
        # If we've gone more than `actor.carefulness` experience points since making a mistake before
        # then we can begin making mistakes again.
        if sum(actor.experiences) - actor.last_mistake_made > actor.carefulness:

            genius = actor.genius if hasattr(actor, 'genius') else self.genius
            learning_point = actor.learning_point if hasattr(actor, 'learning_point') else self.learning_point

            competence_curve = basic_sigmoid(genius=genius,
                                             learning_point=learning_point)
            percentage_competence = competence_curve(sum(actor.experiences))

            degree_experience_needed = sum(actor.experiences) * percentage_competence + actor.carefulness
            mistake_probability_func = generate_mistakes_pmf_with_limit(degree_experience_needed)

            mistake_made_probability = mistake_probability_func(sum(actor.experiences) - actor.carefulness - actor.last_mistake_made)
            if mistake_made_probability > random():
                actor.last_mistake_made = sum(actor.experiences)

                # Set the actor to actually make a mistake
                if percentage_competence < 0.5:
                    actor.mistake_to_make = ('after', repeat_step, 'repeat step')
                else:
                    if isinstance(actor, CustomerServiceActor):
                        actor.number_above_permissions += 1
                    else:
                        actor.mistake_to_make = ('after', remove_previous_action, 'skip step')


                # Plotting, can safely remove
                if actor.actor_name == 'Customer Service Actor 5' and CompetenceModel.show_graphs:
                    mistake_points.append(actor.last_mistake_made)
                    experience_points = reduce(lambda acc, elem: acc + [acc[-1] + elem], actor.experiences, [0])[1:]
                    plt.plot(experience_points, map(competence_curve, experience_points), '-b')
                    plt.plot(mistake_points, map(competence_curve, mistake_points), 'xr')
                    plt.show()
                    pass



        # * Run the actual attribute (in our case, `get_next_task`)
        if actor.number_above_permissions > 0:
            if specialists not in actor.troupes:
                specialists.add_member(actor)
            curr_task = attribute(*args, **kwargs)
            if type(curr_task) is str:
                actor.number_above_permissions -= 1
                for name, method in SpecialistWorkflow.__dict__.items():
                    if name.lower() == curr_task:
                        curr_task = partial(method, actor)
                        task_name = name

                # Log the abnormality
                log_fuzz('acting above permissions', task_name, actor.actor_name)


            actor.troupes.remove(specialists)

        else:
            curr_task = attribute(*args, **kwargs)

        # * Encore
        actor.curr_task = curr_task

        # We have to return the value from the task
        return curr_task

# class ActAbovePermissions(object):
#     def around(self, attribute, actor, *args, **kwargs):
#         '''
#
#         :param actor:
#         :param attribute:
#         :param args:
#         :param kwargs:
#         :return:
#         '''
#         if not hasattr(actor, 'mistake_to_make'):
#             setattr(actor, 'mistake_to_make', None)
#
#         if actor.mistake_to_make is not None and actor.mistake_to_make[2] == 'acting outside permissions':
#
#         else:
#             curr_task = attribute(*args, **kwargs)
#
#         return curr_task


def basic_sigmoid(genius=0.1, learning_point = 50):
    return lambda x: 0.1 + 0.9 / (1 + exp(-genius*(x-learning_point)))


def generate_mistakes_pmf_with_limit(limit):
    def pmf(total_exp):
        '''
        Returns the _probability_ that a mistake will be made, where `limit` represents the maximum experience gained (a shorthand here for work performed) where a mistake will occur.
        Note that this implies a mistake is almost guaranteed to be made...we make that choice deliberately, so we can use a PMF here. It's not necessarily representative of the real world.
        :param total_exp:
        :return:
        '''
        if total_exp <= 0:
            return 0
        if total_exp >= limit:
            return 1


        return min(1, ((3 * limit * (total_exp ** 2) - 2 * (total_exp ** 3)) / limit ** 3))
    return pmf
    
