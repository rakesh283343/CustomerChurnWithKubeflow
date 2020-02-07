import unittest

import pandas as pd
import tensorflow as tf
from train import train
from pathlib import Path


class MyTestCase(unittest.TestCase):
    """
    This method will setup mock data for running different test cases
    """

    def setUp(self) -> None:
        model = train.create_tfmodel(optimizer=tf.optimizers.Adam(),
                                     loss='binary_crossentropy',
                                     metrics=['accuracy'],
                                     input_dim=11)
        self.model = model
        self.bucket = 'gs://kube-1122/customerchurn'
        self.model_path = '/workspace/model/1'
        test_label = pd.Series([1, 0, 0, 1, 0, 1, 1, 1])
        self.testy = test_label
        pred_label = [1, 0, 1, 1, 0, 1, 0, 1]
        self.pred = pred_label
        self.parser = train.parse_arguments()

    '''
    This test case checks for passed arguments to the step
    '''

    def test_validate_arguments(self):
        args = self.parser.parse_args(['--epochs', '-1', '--batch_size', '-2'])
        with self.assertRaises(AssertionError):
            train.validate_arguments(args)

    '''
     This test case will check various attributes of the created model
     It will check the optimizer name and loss function used to create the model
    '''

    def test_model_optimizer_and_loss(self):
        self.assertEquals(self.model.loss, 'binary_crossentropy')
        self.assertIn('Adam', self.model.optimizer.get_config().values())

    '''
    This test case loads the pre-saved model from gs and performs basic testing
    '''

    def test_loadmodel(self):
        # first we will save the model
        train.save_tfmodel_in_gcs(self.model_path, self.model)
        # now load the model back to perform basic testing
        model = tf.saved_model.load(self.model_path)
        # checks the layers in the saved model
        self.assertEquals(len(model.layers), 3)

    '''
    This test case will test the visualization files created by train step to show metrics 
    on kubeflow dashboard
    '''

    def test_create_visualization(self):
        df_cm = train.create_kf_visualization(self.bucket, self.testy, self.pred, 0.85)
        self.assertTrue(True, Path(self.bucket + '/metadata/cm.csv').is_file())
        self.assertTrue(True, Path('/mlpipeline-metrics.json').is_file())

    '''
    This test case check the total layers in model
    '''
    def test_layers_in_model(self):
        self.assertEquals(len(self.model.layers), 3)

    '''
    This test case will test if model saved to a tmp directory is valid format
    '''

    def test_model_is_saved_at_given_dir(self):
        train.save_tfmodel_in_gcs(self.model_path, self.model)
        self.assertTrue(True, tf.saved_model.contains_saved_model(self.model_path))

    '''
    This test case will check the loading of the train/test data into the train step
    It checks if the unique values in test labels and predict labels are same 
    '''
    def test_load_normalize_data(self):
        testX, testy, trainX, trainy = train.load_data(self.bucket)
        self.assertListEqual(list(testy.iloc[:, 0].unique()), list(trainy.iloc[:, 0].unique()))


if __name__ == '__main__':
    unittest.main()
