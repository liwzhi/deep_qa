"""
Memory updaters takes the original question vector, current memory vector and an
aggregated background knowledge vector and combines them to produce an updated memory vector.

All three input vectors should have the same dimensionality, and the output vector should match that
dimensionality.
"""
from collections import OrderedDict

from keras.layers import Dense, Layer

def split_updater_inputs(x, encoding_dim: int):  # pylint: disable=invalid-name
    sentence_encoding = x[:, :encoding_dim]
    current_memory = x[:, encoding_dim:2*encoding_dim]
    attended_knowledge = x[:, 2*encoding_dim:]
    return sentence_encoding, current_memory, attended_knowledge


class SumMemoryUpdater(Layer):
    """
    This MemoryUpdater adds the memory vector and the aggregated knowledge vector, discarding
    the original question vector.

    We can't just do a merge() here because we want to be able to TimeDistribute this layer, so we
    need to do some fancy footwork with the input vector.
    """
    def __init__(self, encoding_dim, name="sum_memory_updater", **kwargs):
        super(SumMemoryUpdater, self).__init__(name=name, **kwargs)
        self.encoding_dim = encoding_dim
        self.mode = 'sum'

    def call(self, x, mask=None):
        _, current_memory, attended_knowledge = split_updater_inputs(x, self.encoding_dim)
        return current_memory + attended_knowledge

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], int(input_shape[1] / 3))

    def get_config(self):
        base_config = super(SumMemoryUpdater, self).get_config()
        config = {'encoding_dim': self.encoding_dim}
        config.update(base_config)
        return config


class DenseConcatNoQuestionMemoryUpdater(Dense):
    """
    Sorry for the horrible name.  If you can think of a better one, submit a PR.

    This MemoryUpdater concatenates only the memory vector and the aggregated knowledge vector,
    then passes them through a Dense layer. The question vector is discarded.

    Because the input to the memory updater is already concatenated, we just remove the question
    representation and then send this through the Dense layer.
    """
    def __init__(self, encoding_dim, name="dense_concat_memory_updater", **kwargs):
        self.encoding_dim = encoding_dim
        super(DenseConcatNoQuestionMemoryUpdater, self).__init__(encoding_dim, name=name, **kwargs)

    def call(self, x, mask=None):
        # For this memory update, we don't need the question encoding. This is the first
        # concatentated vector, so we remove it.
        x = x[:, self.encoding_dim:]
        return super(DenseConcatNoQuestionMemoryUpdater, self).call(x)

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], int(input_shape[1] / 3))

    def get_config(self):
        base_config = super(DenseConcatNoQuestionMemoryUpdater, self).get_config()
        config = {'encoding_dim': self.output_dim}
        config.update(base_config)
        return config


class DenseConcatMemoryUpdater(Dense):
    """
    This MemoryUpdater concatenates the question vector, memory vector and the aggregated knowledge
    vector and then passes them through a Dense layer.

    Because the input to the memory updater is already concatenated, we just remove the question
    represenation and then send this through the Dense layer.
    """
    def __init__(self, encoding_dim, name="dense_concat_memory_updater", **kwargs):
        self.encoding_dim = encoding_dim
        super(DenseConcatMemoryUpdater, self).__init__(encoding_dim, name=name, **kwargs)

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], int(input_shape[1] / 3))

updaters = OrderedDict()  # pylint: disable=invalid-name
updaters['dense_concat'] = DenseConcatMemoryUpdater
updaters['sum'] = SumMemoryUpdater
updaters['dense_concat_no_question'] = DenseConcatNoQuestionMemoryUpdater
