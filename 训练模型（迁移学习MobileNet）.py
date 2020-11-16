# 基本原理：加载图像，并预处理图像（缩小尺寸，归一化等）
#          使用模型库中的MobileNet结构和参数（论文地址：https://arxiv.org/abs/1704.04861）
#          原模型输出的类别是1000，但是本模型输出的类别是4，因此要替换掉原模型的头部
#          再进行训练

# 路径结构,文件夹名称表示图片的类别
#||imagePath
#|----plastic
#        |----image1
#        |----image2
#        ............
#|----metal
#        |----image1
#        |----image2
#        ............
#|----paper
#        |----image1
#        |----image2
#        ............
#|----other
#        |----image1
#        |----image1
#        ............

# #需要安装的库
# tensorflow
# keras
# sklearn
# imutils
# matplotlib
# opencv-python
# argparse

from keras.applications import MobileNetV2,MobileNet
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import RMSprop,SGD
from keras.layers import Input
from keras.models import Model
from keras.preprocessing.image import ImageDataGenerator,img_to_array
from keras.layers.core import Dropout,Flatten,Dense
from keras.utils import to_categorical
import argparse
from sklearn.preprocessing import LabelBinarizer
from imutils import paths
from imutils import paths
import matplotlib.pyplot as plt
import numpy as np
import argparse
import random
import cv2
import os
import keras
import h5py
import numpy as np
import os

width,height = 224,224
dataPaths = "F:\\Dropbox\\Trash"    # 数据集的位置（注意路径中不能有中文名）参照路径结构

#加载图片+预处理图片
def Preprocessed_Image(imagePaths):
    data = []
    labels = []

    # 获取图片的路径
    imagePaths = sorted(list(paths.list_images(imagePaths)))#could not include filename "Chinese" ,"()" "-",etc
    random.seed(8)
    # 打乱图片路径，达到随机读取的
    random.shuffle(imagePaths)
    Images_num = len(imagePaths)
    # print(imagePaths)
    
    # 预处理图像 
    for imagePath in imagePaths:
        #load the image,pre-process it, and store it in the date list
        image = cv2.imread(imagePath)
        #print(imagePath)
        
        # 修改图片尺寸
        image = cv2.resize(image,(width,height))
        image = img_to_array(image)
        data.append(image)
    
        # 给每个图片标上类别号
        label = imagePath.split(os.path.sep)[-2]
        if label == "plastic":
            label = 1
        elif label =="paper":
            label = 2
        elif label == "metal":
            label = 0
        elif label == "other":
            label = 3
        labels.append(label)
      
    # 将图像数据归一化  [0,255] -->[0,1]
    data_norm = np.array(data,dtype="float")/255.0
    labels = np.array(labels)
    classes = 4
    
    # 将数据集划分训练集和测试集
    (train_X,test_X,train_Y,test_Y) = train_test_split(data_norm,labels,test_size=0.25,random_state = 9)
    
    # 将训练集和测试集的类别转化为one-hot形式
    train_Y = to_categorical(train_Y,num_classes=classes)
    test_Y = to_categorical(test_Y,num_classes=classes)
    return (train_X,test_X,train_Y,test_Y)

# 自定义网络头部结构
class FCHeadNet:
  @staticmethod
  def build(baseModel,classes,D):
    # initialize the head model that will be placed on the top of 
    # base ,then add a FC layer
    # 可以自定义接在mobilenet头部的网络结构
    headModel = baseModel.output
    headModel = Flatten(name="flatten")(headModel)
    #headModel = Dense(D,activation="relu")(headModel)
    #headModel = Dropout(0.5)(headModel)
    #headModel = Dense(D,activation="relu")(headModel)
    #headModel = Dropout(0.5)(headModel)
    
    # softmax layer
    headModel =Dense(classes,activation="softmax")(headModel)
    
    return headModel

def main():
    print("[状态]加载图片...")
    (train_X,test_X,train_Y,test_Y)  = Preprocessed_Image(dataPaths)
    # 加载已有的MobileNet模型结构，不保留模型头部
    baseModel = MobileNet(include_top=False,input_tensor = Input(shape=(224,224,3)))
    
    # 自定义网络头部
    headModel = FCHeadNet.build(baseModel,classes=4,D=256)
    
    #构建模型，将Mobile与自定义的尾部拼接
    model = Model(inputs = baseModel.input,outputs = headModel)
    
    # 将原模型的部分冻结住不训练
    for layer in baseModel.layers:
      layer.trainable = False
    
    # 数据增强，数据生成器
    aug = ImageDataGenerator(rotation_range=30, width_shift_range=0.1,
        height_shift_range=0.1, shear_range=0.2, zoom_range=0.2,
        horizontal_flip=True, fill_mode="nearest")
    print("[状态]编译模型...")
    
    model.compile(loss="categorical_crossentropy",optimizer="adam",
                 metrics=["accuracy"])
    
    print("[状态]训练模型...")
    # 训练模型
    model.fit_generator(aug.flow(train_X,train_Y,batch_size=64),validation_data=(test_X,test_Y),epochs = 200,verbose=1,steps_per_epoch =30)

    # 保存模型
    model.save_weights("MobileNet_trash.h5")

if __name__ == '__main__':
    main()
