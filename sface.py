# This file is part of OpenCV Zoo project.
# It is subject to the license terms in the LICENSE file found in the same directory.
#
# Copyright (C) 2021, Shenzhen Institute of Artificial Intelligence and Robotics for Society, all rights reserved.
# Third party copyrights are property of their respective owners.

import cv2 as cv

class SFace:
    def __init__(self, modelPath, disType=0, backendId=0, targetId=0):
        self._modelPath = modelPath
        self._backendId = backendId
        self._targetId = targetId
        self._model = cv.FaceRecognizerSF.create(
            model=self._modelPath,
            config="",
            backend_id=self._backendId,
            target_id=self._targetId)

        self._disType = disType # 0: cosine similarity, 1: Norm-L2 distance
        assert self._disType in [0, 1], "0: Cosine similarity, 1: norm-L2 distance, others: invalid"

        self._threshold_cosine = 0.363
        # self._threshold_norml2 = 1.128
        self._threshold_norml2 = 0.92
        # self._threshold_norml2 = 1.15

    @property
    def name(self):
        return self.__class__.__name__

    def setBackendAndTarget(self, backendId, targetId):
        self._backendId = backendId
        self._targetId = targetId
        self._model = cv.FaceRecognizerSF.create(
            model=self._modelPath,
            config="",
            backend_id=self._backendId,
            target_id=self._targetId)

    def _preprocess(self, image, bbox):
        if bbox is None:
            return image
        else:
            return self._model.alignCrop(image, bbox)
    def get_confidence_score(self, distance, threshold):
        if distance <= threshold:
            return 1 - (distance / threshold)
        else:
            return 0
    def infer(self, image, bbox=None):
        # Preprocess
        inputBlob = self._preprocess(image, bbox)

        # Forward
        features = self._model.feature(inputBlob)
        return features

    def match(self, image1, face1, image2, face2):
        feature1 = self.infer(image1, face1)
        feature2 = self.infer(image2, face2)

        if self._disType == 0: # COSINE
            cosine_score = self._model.match(feature1, feature2, self._disType)
            return cosine_score, True if cosine_score >= self._threshold_cosine else False
        else: # NORM_L2
            norml2_distance = self._model.match(feature1, feature2, self._disType)
            return self.get_confidence_score(norml2_distance, self._threshold_norml2), True if norml2_distance <= self._threshold_norml2 else False
        
    def n_match_cosine(self, features, feature):
        match_list = []
        for fea in features:
            cosine_score = self._model.match(feature, fea, 0)
            res = True if cosine_score >= self._threshold_cosine else False
            match_list.append(res)
        return match_list
    

    def n_match_norml2(self, features, feature):
        """
        
        """
        match_list = []
        confidence_list = []
        for fea in features:
            norml2_score = self._model.match(feature, fea, 1)
            confidence = self.get_confidence_score(norml2_score, self._threshold_norml2)
            res = True if norml2_score <= self._threshold_norml2 else False
            match_list.append(res)
            confidence_list.append(confidence)
        return match_list, confidence_list
    
