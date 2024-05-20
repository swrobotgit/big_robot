#include <Servo.h>

/******___Переменные для работы с сообщениями____******/
//Получили id сообщения
bool parStart = false;
//Начать склейку сообщения
bool mearge = false;
//Сообщение получено полностью
bool mes_successful = false;
//Строка сообщения, полученная по Serial
String msg;
//Число полученное из msg
int mes;
/*******************************************************/



//Создаем объекты типа Servo
Servo Nose; //Нос
Servo Left; //Левая рука
Servo Right; //Правая рука

// Перечеслитель для частей тела
enum Pose {
  RIGHT,
  LEFT,
  NOSE
};

//создаем объект типа Pose, чтобы отличать сообщения (Id сообщения)
Pose Id_mes = NOSE;

void setup() 
{
  //устанавливаем скорость общения
  Serial.begin(9600);
  //конфигурируем выходы и объявляем управляющие пины для Servo моторов
  Nose.attach(8);
  Right.attach(10);
  Left.attach(9);
  
  //параметры по умолчанию
  Nose.write(90);
  Right.write(170);
  Left.write(10);
}

void loop() 
{  
  //отключаем лишние проверки, для ускорения
  while(true)
  {
    //Читаем порт
   if(Serial.available())
   {
      //считываем один символ из порта
      char in = Serial.read();
      //проверка, чтобы убрать влияние '\n' и '\r' на сообщения
      if(!(in == '\n' || in == '\r'))
      {
/***********____Получем сообщения для обработки____**************/   
        //Если приняли символ начала сообщения, то со следущего символа начинаем склейку
        if(parStart) 
        {
          //Начать склейку
          mearge = true;
        } 

     
        //Проверяем на символ начала сообщения
        if(!parStart)
        {
          switch(in)
          {
            case 'R': 
              Id_mes = RIGHT;
              parStart = true;
              break;
            case 'L':
              Id_mes = LEFT;
              parStart = true;
              break;
            case 'N':
              Id_mes = NOSE;
              parStart = true;
              break;
            default:
              break;
          }
        }
        //Проверяем на символ конца сообщения
        else
        {   
            switch(in)
            {
            case ';':
              parStart = false;
              mearge = false;
              mes_successful = true;
              break;
            default:
              break;
            }
        }
  
        //Склейка сообщения
        if(mearge)
        {
          msg += in;
        }

/*******************************************************/
  
/*************____Обрабатывем принятое сообщения____***********/
        if(mes_successful)
        {
          //преобразуем в целое число
          mes = msg.toInt();
          //В зависимости от Id сообщения отпровляем сигнал на соответствующий двигатель
          switch(Id_mes)
          {
            case NOSE: 
               Nose.write(75*mes + 10);
            break;
            case RIGHT: 
               Right.write(180 - 160*mes);
            break;
            case LEFT: 
               Left.write(160*mes+10);
           break;
          default:
            break;
        }
          //окончили обработку сообщения
          mes_successful = false;
          //очищаем сообщения
          msg = ""; 
          }   
/*****************************************************************/  
      } 
    }  
  }  
}
