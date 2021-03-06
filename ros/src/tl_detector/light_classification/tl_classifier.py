import rospy
from styx_msgs.msg import TrafficLight
import cv2
import os
import keras
import numpy as np
from keras.applications import vgg16
from keras.preprocessing.image import img_to_array
from keras.applications.imagenet_utils import decode_predictions
from keras.models import load_model
from keras.models import model_from_yaml
from keras.models import Sequential
from keras.layers import Conv2D, Flatten, Dense, Lambda, MaxPooling2D, Dropout
import tensorflow as tf
import yaml

class TLClassifier(object):
    def __init__(self):
        #TODO load classifier
        #pass
        global tl_model
        global graph_tl
        
        config_string = rospy.get_param("/traffic_light_config")
        self.config = yaml.load(config_string)
        self.is_site = self.config['is_site']
        

        if (not self.is_site):
            
            self.threshold = .7
            #Load the VGG16 model
            # Save the graph after loading the model
            global vgg_model
            vgg_model = vgg16.VGG16(weights='imagenet')
            global graph_vgg
            graph_vgg = tf.get_default_graph()        

            tl_model = Sequential()
            tl_model.add(Lambda(lambda x: x / 127.5 - 1.0, input_shape=(224, 224, 3)))
            tl_model.add(Conv2D(32, (3, 3), strides=(2, 2), activation='relu'))
            tl_model.add(MaxPooling2D(2,2))
            tl_model.add(Conv2D(36, (5, 5), strides=(2, 2), activation='relu'))
            tl_model.add(MaxPooling2D(2,2))
            tl_model.add(Conv2D(48, (5, 5), strides=(2, 2), activation='relu'))
            tl_model.add(Conv2D(64, (3, 3), activation='relu'))
            tl_model.add(Conv2D(64, (3, 3), activation='relu'))
            tl_model.add(Flatten())
            tl_model.add(Dense(100))
            tl_model.add(Dense(50))
            tl_model.add(Dense(10))
            tl_model.add(Dense(3, activation='softmax'))

            os.chdir('.')
            tl_model.load_weights('light_classification/highway_modelv3-ep15-wts.h5')
            graph_tl = tf.get_default_graph()        
            
        else:
            self.threshold = .5

            tl_model = Sequential()
            tl_model.add(Lambda(lambda x: x / 127.5 - 1.0, input_shape=(224, 224, 3)))
            tl_model.add(Conv2D(32, (3, 3), strides=(2, 2), activation='relu'))
            tl_model.add(MaxPooling2D(2,2))
            tl_model.add(Conv2D(36, (5, 5), strides=(2, 2), activation='relu'))
            tl_model.add(MaxPooling2D(2,2))
            tl_model.add(Conv2D(48, (5, 5), strides=(2, 2), activation='relu'))
            tl_model.add(Conv2D(64, (3, 3), activation='relu'))
            tl_model.add(Conv2D(64, (3, 3), activation='relu'))
            tl_model.add(Flatten())
            tl_model.add(Dense(100))
            tl_model.add(Dense(50))
            tl_model.add(Dense(10))
            tl_model.add(Dense(4, activation='softmax'))

            os.chdir('.')
            tl_model.load_weights('light_classification/site_modelv5-ep30-wts.h5')
            graph_tl = tf.get_default_graph()        
        
        print('Traffic light claasifier initialized')
        

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)
        """
        #return TrafficLight.UNKNOWN

        #TODO implement light color prediction
        image224 = cv2.resize(image, (224, 224))
        image224 = cv2.cvtColor(image224, cv2.COLOR_BGR2RGB)
        image224 = img_to_array(image224)
        # Convert the image into 4D Tensor (samples, height, width, channels) by adding an extra dimension to the axis 0.
        input_image = np.expand_dims(image224, axis=0)
        
        if (not self.is_site):
        
            processed_image_vgg16 = vgg16.preprocess_input(input_image.copy())     
            with graph_vgg.as_default():
                predictions_vgg16 = vgg_model.predict(processed_image_vgg16)
            label_vgg16 = decode_predictions(predictions_vgg16)

            if (int(label_vgg16[0][0][1] == 'traffic_light') & int(label_vgg16[0][0][2] > 0.7)):
                # make a prediction
                with graph_tl.as_default():
                    predict = tl_model.predict(input_image)
                    #predict = tl_model.predict(processed_image_vgg16)

                #print('Traffic Light Prediction ', predict[0])
                if predict[0][0] > self.threshold:
                    #print('Classifier Prediction - RED', predict[0][0])
                    rospy.loginfo("   Classifier Prediction - RED %f", predict[0][0])
                    return TrafficLight.RED
                elif predict[0][1] > self.threshold:
                    #print('Classifier Prediction - YELLOW', predict[0][1])
                    rospy.loginfo("   Classifier Prediction - YELLOW %f", predict[0][1])
                    return TrafficLight.YELLOW
                elif predict[0][2] > self.threshold:
                    #print('Classifier Prediction - YELLOW', predict[0][1])
                    rospy.loginfo("   Classifier Prediction - GREEN %f", predict[0][2])
                    return TrafficLight.GREEN
            else:
                #print('Classifier Prediction - UNKNOWN', label_vgg16[0][0])
                #rospy.loginfo("   Classifier Prediction - UNKNOWN [%s, %f]", label_vgg16[0][0][1], label_vgg16[0][0][2])
                return TrafficLight.UNKNOWN
            
        else:       
            # make a prediction
            with graph_tl.as_default():
                predict = tl_model.predict(input_image)

                if predict[0][0] > self.threshold:
                    #print('Classifier Prediction - RED', predict[0][0])
                    rospy.loginfo("   Classifier Prediction - RED %f", predict[0][0])
                    return TrafficLight.RED
                elif predict[0][1] > self.threshold:
                    #print('Classifier Prediction - YELLOW', predict[0][1])
                    rospy.loginfo("   Classifier Prediction - YELLOW %f", predict[0][1])
                    return TrafficLight.YELLOW
                elif predict[0][2] > self.threshold:
                    #print('Classifier Prediction - YELLOW', predict[0][1])
                    rospy.loginfo("   Classifier Prediction - GREEN %f", predict[0][2])
                    return TrafficLight.GREEN
                
                rospy.loginfo("   Classifier Prediction - UNKNOWN %f", predict[0][3])
                return TrafficLight.UNKNOWN
