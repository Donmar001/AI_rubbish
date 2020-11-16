# 基本原理：垃圾被丢进垃圾桶，触发红外模块，触发程序，系统调用训练好的模型对图像进行分类
#           根据模型预测的结果，通过串口发送指令给下位机，控制垃圾桶进行分类操作
#           同时有反馈步骤 + 保存每次预测的图像 （具体原理和步骤详见报告书）

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
#    

from tkinter import *
from PIL import Image,ImageTk
import tkinter.messagebox
import tkinter as tk
import time
import pyautogui
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.imagenet_utils import preprocess_input
from keras.preprocessing.image import img_to_array
import numpy as np
import time
import os
from PIL import Image
import cv2
from multiprocess import Process,Queue
import os,time,random
import RPi.GPIO as GPIO
import serial

# 界面显示的logo图标
logo_path = "/home/pi/Desktop/smart_trash/photo/fly_hero.jpg"
imagePath = "/home/pi/Desktop/Images/"    #图片储存的路径（注意路径中不能有中文名）



labels = ["金属","塑料","废纸","其他"]

time_ok = time.time()
time_yesno = time.time()
time_init = time.time()
sign_yesno = 0
sign_ok = 0
sign_init = 0

#初始化IO口，分别是红外出发端口和LED补光控制端口
GPIO.setmode(GPIO.BCM)
GPIO.setup(21,GPIO.IN)
GPIO.setup(20,GPIO.OUT,initial=GPIO.LOW)
GPIO.setwarnings(False)

#初始化串口，串口连接下位机
ser = serial.Serial("/dev/ttyUSB0",9600,timeout =1)
# 加载已经训练好的模型
happyModel = load_model("/home/pi/Desktop/Models/MobileNet_trash.h5")

#拍照
def capture(count):
    os.system("fswebcam --no-banner -r 640x480 -d /dev/video"+str(count)+" /home/pi/Desktop/Images/test"+str(count)+".jpg")

#图像预处理
def image_preprocess(imagePath):
    image = cv2.imread(imagePath)
    image = cv2.resize(image,(128,128))
    image = image.astype("float")/255.0
    image = img_to_array(image)
    image = np.expand_dims(image,axis=0)
    return image

#压缩图像
def compressed_image(imagePath,weight,height):
    sImag = Image.open(imagePath)
    print(weight,height)
    dImg = sImag.resize((weight,height),Image.ANTIALIAS)
    dImg.save(imagePath)

def Tk_photo(photoPath,weight,height):
    sImag = Image.open(photoPath)
    dImg = sImag.resize((weight,height),Image.ANTIALIAS)
    dImg.save(photoPath.split(".")[0]+"_show."+photoPath.split(".")[1]) #重命名显示的图片
    photo = ImageTk.PhotoImage(dImg)
    return photo


class Popup(tk.Toplevel):
    def __init__(self,parent):
        super().__init__()
        self.title("请给垃圾进行标记～")
        self.parent = parent
        self.geometry("480x360")

        Label(self,text = "请选择您刚才扔的垃圾的类型",font = "Monaco 16",fg="green").place(x=80,y=30)
        
        Button_capture1 = Button(self,text="塑料",font = "Monaco 12",width=8,height=5,command=lambda:self.move_file("plastic"))
        Button_capture2 = Button(self,text="金属",font = "Monaco 12",width=8,height=5,command=lambda:self.move_file("metal"))
        Button_capture3 = Button(self,text="废纸",font = "Monaco 12",width=8,height=5,command=lambda:self.move_file("paper"))
        Button_capture4 = Button(self,text="其他",font = "Monaco 12",width=8,height=5,command=lambda:self.move_file("other"))
        Button_capture1.place(x = 10,y = 100)
        Button_capture2.place(x = 125,y = 100)
        Button_capture3.place(x = 240,y = 100)
        Button_capture4.place(x = 355,y = 100)

    def message_show(self):
        global time_ok,sign_ok,time_init,sign_init
        self.destroy()
        time_ok = time.time()
        sign_ok = 1
        a = tkinter.messagebox.showinfo("谢谢","谢谢您的反馈！\n你的反馈让我变得更智能！")
        time_init = time.time()
        sign_init = 1
    
    # 将每次判断的图像保存到文件夹当中，以增加数据集
    def move_file(self,trash_type):
        os.system("mv /home/pi/Desktop/Images/test0.jpg /home/pi/Desktop/Images/user_label_image/"+trash_type+"/"+str(int(time.time()))+"0"+".jpg")
        os.system("mv /home/pi/Desktop/Images/test1.jpg /home/pi/Desktop/Images/user_label_image/"+trash_type+"/"+str(int(time.time()))+"1"+".jpg")
        
        if trash_type == "plastic":
            ser.write("1".encode(encoding="utf-8"))
        elif trash_type == "paper":
            ser.write("2".encode(encoding="utf-8"))
        elif trash_type == "metal":
            ser.write("3".encode(encoding="utf-8"))
        elif trash_type == "other":
            ser.write("4".encode(encoding="utf-8"))

        if trash_type == "plastic":
            a = "塑料"
        elif trash_type == "paper":
            a = "废纸"
        elif trash_type == "metal":
            a = "金属"
        elif trash_type == "other":
            a = "其他"
        
        self.parent.label_decision.config(text="垃圾种类："+a,font = "Monaco 18",fg="blue")
        self.parent.update()
        self.message_show()
        
class MyApp(tk.Tk):
    
    def __init__(self):
        super().__init__()
        self.title("人工智能图像识别垃圾桶 电协小飞侠队")
        self.geometry("480x360")
        
        self.begin()

    def begin(self):
        a = Tk_photo(logo_path,100,100)
        self.photo_show1 = Label(self,image = a)
        self.photo_show1.image = a
        self.label1 = Label(self,text = "摄像头1：")

        b = Tk_photo(logo_path,100,100)
        self.photo_show2 = Label(self,image = b)
        self.photo_show2.image = b
        self.label2 = Label(self,text = "摄像头2：")

        self.label1.place(x=20,y=10)
        self.photo_show1.place(x=20,y=30)
        self.label2.place(x=20,y=145)
        self.photo_show2.place(x=20,y=165)

        self.label_state = Label(self,text="状态：空闲",font = "Monaco 15",fg="green")
        self.label_decision = Label(self,text="垃圾种类：无",font = "Monaco 18",fg="red")
        self.label_result1 = Label(self,text="等待结果",font = "Monaco 12")
        self.label_result2 = Label(self,text="等待结果1",font = "Monaco 12")
        self.label_result3 = Label(self,text="等待结果2",font = "Monaco 12")
        self.label_result4 = Label(self,text="等待结果3",font = "Monaco 12")

        Label(self,text="置信度：",font = "Monaco 15").place(x = 160,y= 130)
        self.label_state.place(x=160,y=30)
        self.label_decision.place(x=160,y=60)
        self.label_result1.place(x = 160,y= 160)
        self.label_result2.place(x = 160,y= 190)
        self.label_result3.place(x = 160,y= 220)
        self.label_result4.place(x = 160,y= 250)

        Button_capture1 = Button(self,text="点击",font = "Monaco 10",width=8,height=5,command=self.on_click)
        Button_capture1.place(x = 475,y = 130)
    
    def init(self):
        global sign_init,sign_yesno,sign_ok
        sign_init = 0
        sign_yesno = 0
        sign_ok = 0
        a = Tk_photo(logo_path,100,100)
        self.photo_show1 = Label(self,image = a)
        self.photo_show1.image = a
        self.photo_show1.place(x=20,y=30)

        b = Tk_photo(logo_path,100,100)

        self.photo_show2 = Label(self,image = b)
        self.photo_show2.image = b
        self.photo_show2.place(x=20,y=165)
        
        self.label_decision.config(text="垃圾种类：无",font = "Monaco 18",fg="red")
        self.label_result1.config(text="等待垃圾",font = "Monaco 12")
        self.label_result2.config(text="等待垃圾",font = "Monaco 12")
        self.label_result3.config(text="等待垃圾",font = "Monaco 12")
        self.label_result4.config(text="等待垃圾",font = "Monaco 12")

        a = Tk_photo(logo_path,100,100)
        self.photo_show1 = Label(self,image = a)
        self.photo_show1.image = a
        self.label1 = Label(self,text = "摄像头1：")

        b = Tk_photo(logo_path,100,100)
        self.photo_show2 = Label(self,image = b)
        self.photo_show2.image = b
        self.label2 = Label(self,text = "摄像头2：")

    # 促发系统
    def on_click(self):
        global time_yesno,sign_yesno,time_ok,sign_ok,time_init,sign_init
        #拍照+识别
        self.init()
        result = {}
        self.label_state.config(text="状态：正在拍照",font = "Monaco 15",fg="blue")
        self.update()
        GPIO.output(20,1)   #开灯拍照
        time.sleep(1)
        capture(0)
        capture(1)
        GPIO.output(20,0)   #关灯
        self.label_state.config(text="状态：正在识别",font = "Monaco 15",fg="blue")
        self.update()
        image1 = image_preprocess("/home/pi/Desktop/Images/test0.jpg")
        image2 = image_preprocess("/home/pi/Desktop/Images/test1.jpg")
        
        #预测图像，对两个摄像头采集的图像进行预测
        pred1 = happyModel.predict(image1)
        pred2 = happyModel.predict(image2)
        print(pred1)
        print(pred2)
        # 平均两个预测结果
        for i in range(4):
            result[labels[i]] = float(pred1[0][i] + pred2[0][i])
            result[labels[i]] = round(result[labels[i]]*100/2,2)
        sorted_r = sorted(result.items(),key=lambda result:result[1])

        a = Tk_photo("/home/pi/Desktop/Images/test0.jpg",100,100)
        self.photo_show1 = Label(self,image = a)
        self.photo_show1.image = a
        self.photo_show1.place(x=20,y=30)
        
        b = Tk_photo("/home/pi/Desktop/Images/test1.jpg",100,100)
        self.photo_show2 = Label(self,image = b)
        self.photo_show2.image = b
        self.photo_show2.place(x=20,y=165)

        self.label_decision.config(text="垃圾种类："+str(sorted_r[-1][0]),font = "Monaco 18",fg="blue")
        self.label_result1.config(text="1."+sorted_r[-1][0]+":"+str(sorted_r[-1][1])+"%",fg="green")
        self.label_result2.config(text="2."+sorted_r[-2][0]+":"+str(sorted_r[-2][1])+"%")
        self.label_result3.config(text="3."+sorted_r[-3][0]+":"+str(sorted_r[-3][1])+"%")
        self.label_result4.config(text="4."+sorted_r[-4][0]+":"+str(sorted_r[-4][1])+"%")
        
        time_yesno = time.time()
        sign_yesno = 1
        YN = tkinter.messagebox.askyesno(title="请问",message="识别结果是:\n\n"+"    "+sorted_r[-1][0]+"\n\n请问正确吗？")
        
        
        self.label_state.config(text="状态：空闲",font = "Monaco 15",fg="green")
        self.update()
        if YN == False:
            sign_yesno = 0
            pw = Popup(self)
            self.wait_window(pw)
            
        else:
            if sorted_r[-1][0] == "塑料":
                trash_type = "plastic"
            elif sorted_r[-1][0] == "金属":
                trash_type = "metal"
            elif sorted_r[-1][0] == "其他":
                trash_type = "other"
            elif sorted_r[-1][0] == "废纸":
                trash_type = "paper"

            if sorted_r[-1][0] == "塑料":
                ser.write("1".encode(encoding="utf-8"))
            elif sorted_r[-1][0] == "废纸":
                ser.write("2".encode(encoding="utf-8"))
            elif sorted_r[-1][0] == "金属":
                ser.write("3".encode(encoding="utf-8"))
            elif sorted_r[-1][0] == "其他":
                ser.write("4".encode(encoding="utf-8"))
            
            os.system("mv /home/pi/Desktop/Images/test0.jpg /home/pi/Desktop/Images/user_label_image/"+trash_type+"/"+str(int(time.time()))+"0"+".jpg")
            os.system("mv /home/pi/Desktop/Images/test1.jpg /home/pi/Desktop/Images/user_label_image/"+trash_type+"/"+str(int(time.time()))+"1"+".jpg")
            time_ok = time.time()
            sign_ok = 1
            tkinter.messagebox.showinfo("谢谢","谢谢您的反馈！\n你的反馈让我变得更加智能！")
            time_init = time.time()
            sign_init = 1

def main():
    global time_yesno,time_ok,time_init,sign_yesno,sign_ok,sign_init
    if GPIO.input(21)==0:
        time.sleep(0.15)
        if GPIO.input(21)==0:
            pyautogui.click(x = 495,y = 215)
            print("4")
            pyautogui.click(x = 480,y = 320)
    if ((time.time()-time_yesno) >5) and (sign_yesno == 1):
        sign_yesno = 0
        pyautogui.press("enter")
        print("1")
    if ((time.time()-time_ok) >2) and (sign_ok == 1):
        sign_ok = 0
        pyautogui.press("enter")
        print("2")
    if ((time.time()-time_init) >8) and (sign_init == 1):
        sign_init = 0
        app.init()
        print("3")
    app.after(1,main)


if __name__ == '__main__':
    app = MyApp()
    app.after(1,main)
    app.mainloop()



