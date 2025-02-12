import pefile
import ember
# from .ember_extractor import PEFeatureExtractor
import numpy as np
def extract_features(data):
    """
    Extract features from the given binary data (a byte string).

    :param data: The binary data from which to extract features.
    :return: A list of feature values.
    """
    extractor = ember.PEFeatureExtractor(2)
    features = np.array(extractor.feature_vector(data), dtype=np.float32)
    pe = pefile.PE(data=data)
    return [features], list(pe.header)

    