'''
Assembler class, responsible for generating a single trackable object
to simplify the main file design and eliminate various types of errors.

@author Konstantinos Iliakis
@date 16.01.2019
'''

import abc


class Stage(metaclass=abc.ABCMeta):
    """
    Define an interface for handling requests.
    Implement the successor link.
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    def track(self, *args, **kwargs):
        pass


class Profile(Stage):
    def track(self, *args, **kwargs):
        print('[%s] Tracking' % (type(self).__name__))


class TotalInducedVoltage(Stage):
    def track(self, *args, **kwargs):
        print('[%s] Tracking' % (type(self).__name__))


class Plot(Stage):
    def track(self, *args, **kwargs):
        print('[%s] Tracking' % (type(self).__name__))


class BunchMonitor(Stage):
    def track(self, *args, **kwargs):
        print('[%s] Tracking' % (type(self).__name__))


def kick(*args, **kwargs):
    print('[%s] Tracking' % ('kick'))


def linear_interp_kick(*args, **kwargs):
    print('[%s] Tracking' % ('linear_interp_kick'))


def drift(*args, **kwargs):
    print('[%s] Tracking' % ('drift'))


def rf_voltage_calculation(*args, **kwargs):
    print('[%s] Tracking' % ('rf_voltage_calculation'))


def _getType(obj):
    return type(obj).__name__


def _getOrder(obj):
    try:
        order = _order.index(_getType(obj))
    except ValueError as e:
        order = len(_order)
    return order


class Tracker():
    '''
    This is the master tracking object.
    It is constructed by the assembler.
    Tracker is responsible for the pipeline of the modules, respecting the
    pre-defined order.
    The user calls its track method.
    '''

    def __init__(self, *stages, **kwargs):
        self.pipeline = []
        self.turn = 0

        stage_list = list(stages)

        # 1st goest the profile
        self.profile = self.add_stage(stage_list, class_str='Profile')

        # then the induced voltage
        self.totalInducedVoltage = self.add_stage(
            stage_list, class_str='TotalInducedVoltage')

        # the Beam FB
        self.beamFeedback = self.add_stage(stage_list, class_str='BeamFeedback')

        # Cacity FB
        self.spsCavityFeedback = self.add_stage(
            stage_list, class_str='SPSCavityFeedback')
        self.spsOneTurnFeedback = self.add_stage(
            stage_list, class_str='SPSOneTurnFeedback')

        # Noise FB
        self.lhcNoiseFB = self.add_stage(stage_list, class_str='LHCNoiseFB')

        # the periodicity
        # if (interpolation) or induced voltage or cavity FB then
        if (self.totalInducedVoltage) or (self.spsCavityFeedback) or (self.spsOneTurnFeedback):
            # the rf voltage caclulation
            self.appendStage(rf_voltage_calculation)
            self.appendStage(linear_interp_kick)
        else:
            self.appendStage(kick)

        self.appendStage(drift)
        # then the tracking
        # then the tracking

        # then monitors
        self.bunchMonitor = self.add_stage(stage_list, class_str='BunchMonitor')

        # finally the plots
        self.plot = self.add_stage(stage_list, class_str='Plot')

    def __call__(self, *args, **kwargs):
        '''
        Makes the object callable.
        '''
        self.track(*args, **kwargs)

    # Check for the object of type class_str in the given stages, if found
    # then add it to the pipeline, remove it from the stages and return true
    # otherwise return false
    # TODO stages should be a list

    def add_stage(self, stages, class_str):
        for i, stage in enumerate(list(stages)):
            if _getType(stage) == class_str:
                self.pipeline.append(stage.track)
                # self.pipeline_names.append(stage.__name__)
                return stages.pop(i)
        return None

    def printPipeline(self):
        '''
        Print the constructed pipeline
        '''
        # TODO: Add logging
        string = '[Tracker] Pipeline: ['
        for stage in self.pipeline:
            if (getattr(stage, 'track', None) and callable(stage.track)):
                string += '{}.track() --> '.format(_getType(stage))

            elif (callable(stage)):
                string += '{}() --> '.format(stage.__name__)
            else:
                # TODO: Add logging
                sys.exit(
                    '[Tracker]: Error, object of class {} is not callable or track()-able'.format(__getType(stage)))

        if '-->' in string:
            string = string[:-len(' --> ')]
        string += ']'
        # Logging here
        print(string)

    def track(self, *args, **kwargs):
        '''
        Iterate over the callable objects in the pipeline.
        '''
        for stage in self.pipeline:
            stage(*args, **kwargs)

        # Finally progress by 1 turn
        self.turn += 1

    def appendStage(self, stage):
        '''
        Add a new stage to the pipeline
        '''
        if (getattr(stage, 'track', None) and callable(stage.track)):
            self.pipeline.append(stage.track)
            # self.pipeline_names.append(_getType(stage))
        elif (callable(stage)):
            self.pipeline.append(stage)
            # self.pipeline_names.append(stage.__name__)
        else:
            # TODO: Add logging
            sys.exit(
                '[Tracker]: Error, object of class {} is not callable or track()-able'.format(__getType(stage)))


class Assembler():

    def __init__(self):
        pass

    def construct(self, *args, **kwargs):
        tracker = Tracker(*args, **kwargs)
        return tracker



if __name__ == '__main__':

    assembler = Assembler()

    print('\nTracker 1')
    tracker = assembler.construct(
        TotalInducedVoltage(), Plot(), Profile(), BunchMonitor())
    tracker.printPipeline()


    print('\nTracker 2')
    tracker = assembler.construct(Plot(), Profile(), BunchMonitor())
    tracker.printPipeline()
    tracker.track()
