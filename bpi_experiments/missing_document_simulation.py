from bpi_13_experimental_frontend import *

class MissingDocsExperiment(object):
    docs_missing = dict()

    def __init__(self, on_missing_document=lambda _, __: None):
        super(MissingDocsExperiment, self).__init__()
        self.missing_doc_resolution = on_missing_document

    def should_remove_document(self, task):
        '''
        Should return whether the document a current task might emit should be removed.
        :return: A bool, indicating the removal of a document the current task emits.
        '''
        return False

    def on_missing_document(self, task, actor):
        '''
        Parameterises what an agent should do when a given document is missing.
        :return:
        '''
        self.missing_doc_resolution(task, actor)

    def encore(self, task, actor, _result):
        if self.should_remove_document(task):
            pass  # TODO: remove document



