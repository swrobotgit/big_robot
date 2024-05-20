# пример запуска файла: python manual_robot.py --camera /dev/video2 --arduino /dev/ttyUSB0
# код написан для запуска под ubuntu
import cv2
import mediapipe as mp
import serial
import time
import argparse

#Отправляем сообщение
def mesOut(mes):
    mes = bytes(str(mes), 'utf-8')
    try:    
        uart.write(mes)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raisegit

#Формируем сообщение
def preMes(last_value, cur_val, symbol_begin):
    if last_value != cur_val:
        last_value = cur_val
        msg = symbol_begin + str(last_value) + ';'
        mesOut(msg)
    return last_value

if __name__ == "__main__":

    # Парсер
    #--------------------------------
    parser = argparse.ArgumentParser(description='Hello Robot')

    parser.add_argument(
    '--camera',
    type=str,
    required=True,
    help='Device camera, example /dev/video0')

    parser.add_argument(
    '--arduino',
    type=str,
    required=True,
    help='Device arduino, example /dev/ttyUSB0')

    parser.add_argument(
    '--baudurate',
    type=int,
    default=9600,
    help='Baudurate arduino, defult 9600')

    parser.add_argument(
    '--width_frame',
    type=int,
    default=640,
    help='Width frame, defult 640')

    parser.add_argument(
    '--height_frame',
    type=int,
    default=480,
    help='Height frame, defult 480')

    namespace_device = parser.parse_args()
    #-----------------------------------------------

    print("Press Q to end the program.")
    print(f'For help, use "--help".')
    #подключаем камеру
    camera = cv2.VideoCapture(namespace_device.camera)
    if not camera.isOpened():
        print("Cannot open camera!")
        print("Check the device camera, ", end="")
        print(f'current device camera: "{namespace_device.camera}"')
        exit(1)
    ret_width = camera.set(cv2.CAP_PROP_FRAME_WIDTH, namespace_device.width_frame)
    ret_height = camera.set(cv2.CAP_PROP_FRAME_HEIGHT, namespace_device.height_frame)

    #Настраиваем модель
    mpPose = mp.solutions.pose
    Pose = mpPose.Pose(static_image_mode=False,
                    model_complexity=1)

    #утилита для отображения результатов
    mpDraw = mp.solutions.drawing_utils

    #Конфигурируем последовательный порт
    uart = None
    try:
        uart = serial.Serial(namespace_device.arduino, namespace_device.baudurate)
    except serial.SerialException:
        print("Arduino can not be found or can not be configure")
        print("Check the port, ", end="")
        print(f'current port: "{namespace_device.arduino}", current baudurate: {namespace_device.baudurate}!')
        camera.release()
        exit(1)
        
    #Переменные для хранения текущего и предыдущего значения для частей тела
    lastValL = 0
    lastValR = 0
    lastValN = 0
    curValueL = 0
    curValueR = 0
    curValueN = 0


    #Ждем после подключения к Arduino по Serial
    time.sleep(1)
    while True:
        #Получаем кадр с видеокамеры
        good, img = camera.read()
        if not good:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        #Меняем способ кодирования изображения
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #обрабатываем изображения mediapipe, и возвращаем результат
        resultsPerson = Pose.process(imgRGB)

        #Если получили какие-то результаты
        if resultsPerson.pose_landmarks:

            #получаем координаты нужных точек тела
            width, height, color = img.shape
            x = int(resultsPerson.pose_landmarks.landmark[mpPose.PoseLandmark.RIGHT_SHOULDER].x * height)
            y = int(resultsPerson.pose_landmarks.landmark[mpPose.PoseLandmark.RIGHT_SHOULDER].y * width)
            point_12 = [x,y]
            x = int(resultsPerson.pose_landmarks.landmark[mpPose.PoseLandmark.LEFT_SHOULDER].x * height)
            y = int(resultsPerson.pose_landmarks.landmark[mpPose.PoseLandmark.LEFT_SHOULDER].y * width)
            point_11 = [x,y]
            y = int(resultsPerson.pose_landmarks.landmark[mpPose.PoseLandmark.RIGHT_PINKY].y * width)
            point_18 = y
            y = int(resultsPerson.pose_landmarks.landmark[mpPose.PoseLandmark.LEFT_PINKY].y * width)
            point_17 = y
            x = int(resultsPerson.pose_landmarks.landmark[mpPose.PoseLandmark.NOSE].x * height)
            point_0 = x

            #расстояние от правого плеча до носа
            averge012_x = point_0 - point_12[0]
            #расстояние от левого плеча до носа
            averge011_x = point_11[0] - point_0
            #отношение расстояний, для поворота головы
            ration = averge012_x / (averge011_x + 0.0001)

            #расстояние от ладоней до плечей
            point_1812 = point_18 - point_12[1]
            point_1711 = point_17 - point_11[1]

            #Текст сообщения для правой руки
            if point_1812 < -20:
                curValueL = 1
            else:
                curValueL = 0

            # Текст сообщения для левой руки
            if point_1711 < -20:
                curValueR = 1
            else:
                curValueR = 0

            # Текст сообщения для носа
            if ration < 0.4:
                curValueN = 2
            if ration > 0.8:
                curValueN = 1
            if ration > 1.8:
                curValueN = 0

            try:
                #отправляем сообщения, сохраняя отпраленное сообщение
                lastValL = preMes(lastValL, curValueL, 'L')
                lastValR = preMes(lastValR, curValueR, 'R')
                lastValN = preMes(lastValN, curValueN, 'N')
            except Exception as exp:
                print("An error occurred while sending via serial.")
                break

            # отображаем результат обработки изображения
            mpDraw.draw_landmarks(img, resultsPerson.pose_landmarks, mpPose.POSE_CONNECTIONS)

        #зеркалим изображения
        img = cv2.flip(img, 1)
        #отображаем в окно
        cv2.imshow("Image", img)
        #функция для закрытия окна по клавиши 'q'
        if cv2.waitKey(1) == ord('q'):
            break
    
    camera.release()
    uart.close()
