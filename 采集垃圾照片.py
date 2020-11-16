# 运行平台Raspberry Pi 
# 基本原理:建立一个界面，每扔一次垃圾进垃圾桶，按下界面对应垃圾的类别，
# 摄像头自动采集图像保存到相应的文件夹，拍照过程会有LED补光.

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


from tkinter import *
from PIL import ImageTk
from PIL import Image
import os,time
from multiprocess import Process,Queue,Pool
import RPi.GPIO as GPIO

imagePath = "/home/pi/Desktop/Images/"    #图片储存的路径（注意路径中不能有中文名）

#LED补光IO控制
GPIO.setmode(GPIO.BCM)
GPIO.setup(20,GPIO.OUT,initial=GPIO.LOW)

#每个类别的片找个数计算
count = {}
count["plastic"] = 0
count["metal"] = 0
count["paper"] = 0
count["other"] = 0
counts = 1     #计算垃圾的拍照次数

#裁剪图片
def image_crop_save(photoPath):
    image = Image.open(photoPath)
    image = image.crop((80,0,560,480))
    image.save(photoPath)

#压缩图片，
def compressed_image(imagePath,weight,height):
    sImag = Image.open(imagePath)
    print(weight,height)
    dImg = sImag.resize((weight,height),Image.ANTIALIAS)
    dImg.save(imagePath)

#界面暂存的图像
def Tk_photo(photoPath,weight,height,type):
    sImag = Image.open(photoPath)
    dImg = sImag.resize((weight,height),Image.ANTIALIAS)
    if type == "a":
        dImg.save(imagePath+"0.jpg")
    if type == "b":
        dImg.save(imagePath+"1.jpg") 
    photo = ImageTk.PhotoImage(dImg)
    return photo
    
def init():
    global count
    for root,dirs,files in os.walk(imagePath+"plastic"):
        a = files
        for i in range(len(a)):
            a[i]=int(a[i].split(".")[0])
        try:
            count["plastic"] = max(a) + 1
        except ValueError:
            count["plastic"] = 0
    for root,dirs,files in os.walk(imagePath+"metal"):
        a = files
        for i in range(len(a)):
            a[i]=int(a[i].split(".")[0]) + 1
        try:
            count["metal"] = max(a)
        except ValueError:
            count["metal"] = 0
    for root,dirs,files in os.walk(imagePath+"paper"):
        a = files
        for i in range(len(a)):
            a[i]=int(a[i].split(".")[0]) + 1
        try:
            count["paper"] = max(a)
        except ValueError:
            count["paper"] = 0
    for root,dirs,files in os.walk(imagePath+"other"):
        a = files
        for i in range(len(a)):
            a[i]=int(a[i].split(".")[0]) + 1
        try:
            count["other"] = max(a)
        except ValueError:
            count["other"] = 0

#采集图像过程
def take_photo(trash_type,cam,count):
    global counts
    label_state.config(text="状态：正在拍照",fg = "blue") 
    root.update()
    
    # 调用系统的派宅命令来调用摄像头拍照
    os.system("fswebcam --no-banner -r 640x480 -F 20 -d /dev/video"+str(cam)+" "+ imagePath +trash_type+"/"+str(count)+".jpg")
    #image_crop_save("/home/pi/Desktop/Images/"+trash_type+"/"+str(count)+".jpg")
    #compressed_image("/home/pi/Desktop/Images/"+trash_type+"/"+str(count)+".jpg",640,480)
    a = Tk_photo("/home/pi/Desktop/Images/"+trash_type+"/"+str(count)+".jpg",160,120,"a")
    if cam == 0:
        photo_show1 = Label(root,image = a)
        photo_show1.image = a
        photo_show1.place(x=30,y=30)
    if cam == 1:
        photo_show2 = Label(root,image = a)
        photo_show2.image = a
        photo_show2.place(x=30,y=230)
    counts +=1

    #每个垃圾分别采集10张图片，归零
    if counts == 11:
        counts = 1    
    
    label_state.config(text="状态：空闲",fg = "green")
    
    #每次归零后提示"扔另一个垃圾"
    if counts == 1:
        label_counts.config(text="次数"+str(counts)+"(请扔另一个垃圾!!!)",fg = "red")
    else:
        label_counts.config(text="次数"+str(counts),fg = "green")
    
    #更新状态
    root.update()

def take(trash_type):
    global count
    GPIO.output(20,GPIO.HIGH)
    t = time.time() 
    count[trash_type] +=1
    take_photo(trash_type,0,count[trash_type])
    count[trash_type] +=1
    take_photo(trash_type,1,count[trash_type])
    
    print("start")
    print(str((time.time()-t)*1000)+"ms")
    GPIO.output(20,GPIO.LOW)

def main():
    root = Tk()
    root.title("智能图像识别垃圾桶   电子科技协会")
    root.geometry("800x600")
    init()
    print(count["plastic"])
    print(count["metal"])
    print(count["paper"])
    print(count["other"])
    
    #a = Tk_photo(logo_path,168,168)
    #photo_show1 = Label(root,image = a)
    #photo_show1.image = a
    label1 = Label(root,text = "摄像头1：")
    
    #b = Tk_photo(logo_path,168,168)
    #photo_show2 = Label(root,image = b)
    #photo_show2.image = b
    label2 = Label(root,text = "摄像头2：")
    
    #界面按钮对象
    Button1 = Button(root,text="塑料",font = "Monaco 12",width=10,height=5,command=lambda:take("plastic",))
    Button2 = Button(root,text="纸张",font = "Monaco 12",width=10,height=5,command=lambda:take("paper",))
    Button3 = Button(root,text="金属",font = "Monaco 12",width=10,height=5,command=lambda:take("metal",))
    Button4= Button(root,text="其他",font = "Monaco 12",width=10,height=5,command=lambda:take("other",))
    
    #状态栏
    label1.place(x=30,y=10)
    #photo_show1.place(x=30,y=30)
    label2.place(x=30,y=210)
    #photo_show2.place(x=30,y=230)
    
    #Label(root,text="识别结果：",font = "Monaco 16").place(x = 210,y= 240)
    
    label_state = Label(root,text="状态：空闲",font = "Monaco 16",fg="green")
    label_state.place(x=400,y=200)
    
    label_counts = Label(root,text="次数：1",font = "Monaco 16",fg="green")
    label_counts.place(x=400,y=250)
    
    #界面按钮位置
    Button1.place(x = 240,y = 50)
    Button2.place(x = 380,y = 50)
    Button3.place(x = 520,y = 50)
    Button4.place(x = 660,y = 50)
    
    root.mainloop()

if __name__ == '__main__':
    main()
