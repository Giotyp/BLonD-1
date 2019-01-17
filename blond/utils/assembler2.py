'''
Assembler class, responsible for generating a single trackable object
to simplify the main file design and eliminate various types of errors.

@author Konstantinos Iliakis
@date 16.01.2019
'''

import abc

_order = ['Profile', 'TotalInducedVoltage', 'FullRingAndRF', 'RingAndRFTracker',
          'BunchMonitor', 'Plot']


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

    def __init__(self, *stages):
        self.__pipeline = []
        self.__pipeline_names = []
        # self.__trackables = []
        # self.__callables = []
        self.turn = 0
        # self.profile = profile
        # self.rfTracker = rfTracker
        # self.totalInducedVoltage = totalInducedVoltage
        # self.beam = beam
        # self.ring = ring
        # self.bunchMonitor = bunchMonitor
        # self.rfStation = rfStation

        for stage in stages:
            pos = 0
            for currStage in self.__pipeline:
                if _getOrder(currStage) > _getOrder(stage):
                    break
                pos+=1

            if (getattr(stage, 'track', None) and callable(stage.track)):
                self.__pipeline.insert(pos, stage.track)
                self.__pipeline_names.append(_getType(stage))
            elif (callable(stage)):
                self.__pipeline.insert(pos, stage)
                self.__pipeline_names.append(stage.__name__)
            else:
                # TODO: Add logging
                sys.exit(
                    '[Assembler]: Error, object of class {} is not callable or track()-able'.format(__getType(stage)))


    def __call__(self, *args, **kwargs):
        '''
        Makes the object callable.
        '''
        self.track(*args, **kwargs)

    def printPipeline(self):
        '''
        Print the constructed pipeline
        '''
        # TODO: Add logging
        string = '[Tracker] Pipeline:\n['
        for stage_name in self.__pipeline_names:
            string += stage_name + ' --> '
        if '-->' in string:
            string = string[:-len(' --> ')]
        string += ']'
        print(string)

    def track(self, *args, **kwargs):
        '''
        Iterate over the callable objects in the pipeline.
        '''
        for stage in self.__pipeline:
            stage(*args, **kwargs)

        # Finally progress by 1 turn
        self.turn += 1

    def appendStage(self, stage):
        '''
        Add a new stage to the pipeline
        '''
        if (getattr(stage, 'track', None) and callable(stage.track)):
            self.__pipeline.append(stage.track)
            self.__pipeline_names.append(_getType(stage))
        elif (callable(stage)):
            self.__pipeline.append(stage)
            self.__pipeline_names.append(stage.__name__)
        else:
            # TODO: Add logging
            sys.exit(
                '[Assembler]: Error, object of class {} is not callable or track()-able'.format(__getType(stage)))

    # def insertStage(self, stage):
    #     '''
    #     Add a new stage to the pipeline
    #     '''
    #     if Tracker.__getType(stage) not in Tracker.__order:
    #         print(("[Tracker] %s stage not recognised. It will be placed" +
    #                " in the end of the pipeline") % Tracker.__getType(stage))
    #     i = 0
    #     for currStage in self.pipeline:
    #         if Tracker.__getOrder(currStage) > Tracker.__getOrder(stage):
    #             break
    #         i+=1
    #     self.pipeline.insert(i, stage)

    #     return self

    # def insertBefore(self, existingStage, newStage):
    #     '''
    #     Add new stage right before existingStage
    #     '''
    #     try:
    #         pos = self.pipeline.index(existingStage)
    #         self.pipeline.insert(pos, newStage)
    #     except ValueError as e:
    #         raise RuntimeError('[Tracker] %s stage not found in the pipiline' %
    #                            Tracker.__getType(existingStage))
    #     return self

    # def insertAfter(self, existingStage, newStage):
    #     '''
    #     Add new stage right after existingStage
    #     '''
    #     try:
    #         pos = self.pipeline.index(existingStage)
    #         self.pipeline.insert(pos+1, newStage)
    #     except ValueError as e:
    #         raise RuntimeError('[Tracker] %s stage not found in the pipiline' %
    #                             Tracker.__getType(existingStage))
    #     return self

    # def removeStage(self, stage):
    #     '''
    #     Remove (firs occurence of) stage from the pipeline
    #     '''
    #     try:
    #         self.pipeline.remove(stage)
    #     except ValueError as e:
    #         raise RuntimeError('[Tracker] %s stage not found in the pipiline' %
    #                            Tracker.__getType(stage))
    #     return self


class Assembler():

    def __init__(self):
        pass

    def construct(self, **kwargs):
        tracker = Tracker(**kwargs)
        return tracker


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


# class Profile(Stage):
#     def track(self, *args, **kwargs):
#         print('[%s] Tracking turn: %d' % (type(self).__name__, kwargs['turn']))


# class RFTracker(Stage):
#     def track(self, *args, **kwargs):
#         print('[%s] Tracking turn: %d' % (type(self).__name__, kwargs['turn']))


# class TotalInducedVoltage(Stage):
#     def track(self, *args, **kwargs):
#         print('[%s] Tracking turn: %d' % (type(self).__name__, kwargs['turn']))


# assembler = Assembler()

# tracker = assembler.construct(profile=Profile(),
#                               rfTracker=RFTracker(),
#                               totalInducedVoltage=TotalInducedVoltage())
# tracker.printPipeline()
